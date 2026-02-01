from __future__ import annotations

import abc
import enum
import os.path
import time
import subprocess
from .. import Devutils as dev
from . import ManagedJobQueues as queues

__all__ = [
    "ExecutionStatus",
    "ExecutionQueue",
    "ExecutionEngine",
    # "PoolSubmissionEngine",
    "ManagedJobQueueExecutionEngine",
    "SLURMExecutionEngine"
]

class ExecutionStatus(enum.Enum):
    UNKNOWN = "unknown"
    RUNNING = "running"
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"

class ExecutionFuture(metaclass=abc.ABCMeta):
    poll_time = 1
    def __init__(self, poll_time=None):
        self.status = ExecutionStatus.UNKNOWN
        self._is_complete = False
        self._result = None
        self.poll_time = self.poll_time if poll_time is None else poll_time
    def join(self, timeout=None):
        self.status = self.get_status()
        cur = time.time()
        while self.status in {ExecutionStatus.UNKNOWN, ExecutionStatus.RUNNING, ExecutionStatus.PENDING}:
            time.sleep(self.poll_time)
            self.status = self.get_status()
            if timeout is not None:
                now = time.time()
                if now - cur > timeout:
                    raise TimeoutError(f"job {self} timed out during join")
    @abc.abstractmethod
    def get_result(self) -> dict:
        ...
    @abc.abstractmethod
    def get_status(self) -> ExecutionStatus:
        ...

class JoinableExecutionFuture(ExecutionFuture):
    @abc.abstractmethod
    def await_result(self, timeout=None):
        ...
    def join(self, timeout=None):
        self.await_result(timeout=timeout)

class ExecutionQueue:
    def __init__(self, futures:list[ExecutionFuture]):
        self.futures = futures
    def join(self, timeout=None):
        for j in self.futures:
            cur = time.time()
            j.join(timeout=timeout)
            if timeout is not None:
                timeout = timeout - (time.time() - cur)
                if timeout < 0:
                    raise TimeoutError(f"pool {self} timed out during join")

class ExecutionEngine(metaclass=abc.ABCMeta):
    name: str
    future_type: type[ExecutionFuture]
    engine_types = {}
    @classmethod
    def register(cls, name, engine=None):
        if engine is None:
            if isinstance(name, str):
                def register(engine):
                    return cls.register(name, engine)
                return register
            elif isinstance(name, ExecutionEngine):
                engine = name
                return cls.register(engine.name, engine)
        else:
            cls.engine_types[name] = engine
        return engine
    @classmethod
    def resolve(cls, name, **opts):
        return cls.engine_types[name](**opts)

    def __init__(self, **opts):
        self._call_depth = 0
        self.opts = opts

    @abc.abstractmethod
    def submit_job(self, **kwargs) -> ExecutionFuture:
        ...

    def submit_jobs(self, jobs: list[dict], **kwargs) -> ExecutionQueue:
        return ExecutionQueue([
            self.submit_job(**dict(job, **kwargs))
            for job in jobs
        ])

    def __enter__(self):
        # here to be extended
        self._call_depth += 1
        if self._call_depth == 1:
            self.startup()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._call_depth -= 1
        if self._call_depth < 1:
            self.shutdown()

    def startup(self):
        ...

    def shutdown(self):
        ...

class FileBackedExecutionFuture(ExecutionFuture):
    results_file = 'results.json'
    status_file = 'status.json'
    def __init__(self,
                 watch_dir=None,
                 poll_time=None,
                 results_file=None,
                 status_file=None):
        super().__init__(poll_time=poll_time)
        self.watch_dir = watch_dir
        if results_file is None:
            results_file = self.results_file
        self.results_file = results_file
        if status_file is None:
            status_file = self.status_file
        self.status_file = status_file
    def get_result(self) -> dict:
        if self.watch_dir is None:
            results_file = self.results_file
        else:
            results_file = os.path.join(self.watch_dir, self.results_file)
        return dev.read_json(results_file)
    def get_status(self) -> ExecutionStatus:
        if self.watch_dir is None:
            status_file = self.status_file
        else:
            status_file = os.path.join(self.watch_dir, self.status_file)
        if os.path.isfile(status_file):
            stat_dict = dev.read_json(status_file)
            return ExecutionStatus(stat_dict.get('status', 'UNKNOWN'))
        else:
            return ExecutionStatus.UNKNOWN

class ManagedJobQueueExecutionFuture(FileBackedExecutionFuture):
    def __init__(self,
                 job_id,
                 queue_manager:queues.ManagedJobQueueHandler,
                 watch_dir=None,
                 results_file=None,
                 status_file=None,
                 poll_time=None):
        super().__init__(
            watch_dir=watch_dir, poll_time=poll_time,
            results_file=results_file,
            status_file=status_file
        )
        self.queue_manager = queue_manager
        self.job_id = job_id

    queue_status_map = {
        queues.ManagedJobQueueJobStatus.PENDING:ExecutionStatus.PENDING,
        queues.ManagedJobQueueJobStatus.COMPLETED:ExecutionStatus.COMPLETED,
        queues.ManagedJobQueueJobStatus.RUNNING:ExecutionStatus.RUNNING,
        queues.ManagedJobQueueJobStatus.ERROR:ExecutionStatus.ERROR,
    }
    def get_status(self) -> ExecutionStatus:
        return self.queue_status_map[
            self.queue_manager.get_job_status(self.job_id)
        ]

class ManagedJobQueueExecutionEngine(ExecutionEngine):
    future_type = ManagedJobQueueExecutionFuture
    def __init__(self, queue_manager:queues.ManagedJobQueueHandler, **opts):
        super().__init__(**opts)
        self.queue_manager = queue_manager

    def prep_future_opts(self,
                         watch_dir=None,
                         results_file=None,
                         status_file=None,
                         poll_time=None,
                         **kwargs):
        return dict(
            watch_dir=watch_dir,
            results_file=results_file,
            status_file=status_file,
            poll_time=poll_time
        ), kwargs

    def submit_job(self, *,
                   watch_dir=None, poll_time=None,
                   results_file=None,
                   status_file=None,
                   **kwargs) -> ManagedJobQueueExecutionFuture:
        #TODO: track output files
        fut_opts, job_opts = self.prep_future_opts(**kwargs)
        id = self.queue_manager.submit_job(**job_opts)
        return self.future_type(
            id,
            self.queue_manager,
            **fut_opts
        )

class SLURMExecutionFuture(ManagedJobQueueExecutionFuture):
    def get_status(self) -> ExecutionStatus:
        if self.status in {ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED, ExecutionStatus.ERROR}:
            try:
                return super().get_status()
            except KeyError: # job no longer exists because it's done or errored
                return ExecutionStatus.COMPLETED
        else:
            return super().get_status()

class SLURMExecutionEngine(ManagedJobQueueExecutionEngine):
    future_type = SLURMExecutionFuture
    def __init__(self, **opts):
        super().__init__(queues.SLURMHandler(), **opts)

    def prep_future_opts(self, *,
                         sbatch_file,
                         watch_dir=None,
                         chdir=None, **kwargs):
        if watch_dir is None:
            if chdir is None:
                watch_dir = os.path.dirname(sbatch_file)
            else:
                watch_dir = chdir

        return super().prep_future_opts(
            watch_dir=watch_dir,
            chdir=chdir,
            sbatch_file=sbatch_file,
            **kwargs
        )

    def submit_job(self,
                   sbatch_file,
                   *,
                   watch_dir=None, poll_time=None,
                   results_file=None,
                   status_file=None,
                   **kwargs) -> ManagedJobQueueExecutionFuture:
        #TODO: track output files
        fut_opts, job_opts = self.prep_future_opts(sbatch_file=sbatch_file, **kwargs)
        id, _ = self.queue_manager.submit_job(**job_opts)
        return self.future_type(
            id,
            self.queue_manager,
            **fut_opts
        )

class ProcessExecutionFuture(JoinableExecutionFuture):
    def __init__(self, base_obj, **ignored):
        super().__init__(**ignored)
        self.obj = base_obj
        self._get_result = dev.default
    def await_result(self, timeout=None):
        if dev.is_default(self._get_result, allow_None=False):
            self._get_result = self.obj.get(timeout=timeout)
    def get_result(self):
        if dev.is_default(self._get_result):
            return None
        else:
            return self._get_result
    def get_status(self) -> ExecutionStatus:
        try:
            res = self.obj.successful()
        except (ValueError, AssertionError):
            return ExecutionStatus.RUNNING
        else:
            if res:
                return ExecutionStatus.COMPLETED
            else:
                return ExecutionStatus.ERROR

class ProcessGeneratorExecutionEngine(ExecutionEngine):
    future_type = ProcessExecutionFuture
    def __init__(self, proc_gen, **opts):
        super().__init__(**opts)
        self.proc_gen = proc_gen

    def submit_job(self, method, **kwargs):
        # TODO: track output files
        proc = self.proc_gen.apply_async(method, **kwargs)
        return self.future_type(
            proc
        )

    def startup(self):
        self.proc_gen.__enter__()

    def shutdown(self):
        self.proc_gen.__exit__()
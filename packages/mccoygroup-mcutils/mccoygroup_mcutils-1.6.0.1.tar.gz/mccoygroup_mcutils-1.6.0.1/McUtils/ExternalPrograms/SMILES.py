import functools
import multiprocessing

from .. import Devutils as dev
import numpy as np
import multiprocessing as mp

__all__ = [
    "SMILESSupplier",
    "consume_smiles_supplier",
    "match_smiles_supplier"
]

class SMILESSupplier:
    def __init__(self, smiles_file, line_indices=None, size=int(1e3), split_idx=0):
        self.smi = dev.StreamInterface(smiles_file)
        self.line_indices = line_indices
        self._size = size
        self._call_depth = 0
        self._stream = None
        self._cur = None
        self._max_offset = None
        self._offsets:np.ndarray[(None,), int] = None
        self._flexible_offsets = None
        self._assignable_offsets = None
        self.split_idx = split_idx

    def __enter__(self):
        self._call_depth += 1
        if self._call_depth == 1:
            self._stream = self.smi.__enter__()
            self._cur = 0
            if self.line_indices is None:
                #TODO: add an array offset style index to this
                #      in case the SMI file is too big for even uint64
                self._max_offset = 0
                self.line_indices = np.zeros(self._size, dtype='uint64')
            if isinstance(self.line_indices, np.ndarray):
                self._offsets = self.line_indices
                self._flexible_offsets = True
                self._assignable_offsets = True
            else:
                self._offsets = np.load(self.line_indices, mmap_mode='r')
                self._flexible_offsets = False
                self._assignable_offsets = False
            if self._max_offset is None:
                self._max_offset = len(self._offsets)
        return self._stream
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._call_depth -= 1
        if self._call_depth == 0:
            self._cur = None
            self._stream.__exit__(exc_type, exc_val, exc_tb)
            self._stream = None
            if self._flexible_offsets:
                self.line_indices = self._offsets
            self._offsets = None

    def __len__(self):
        with self:
            if self._flexible_offsets:
                self.create_line_index(return_index=False)
                return self._max_offset
            else:
                return self._max_offset
    @classmethod
    def _consume_next(self, db, split_idx=0):
        line = db.readline()
        if len(line) == 0:
            return line
        else:
            return line.split(maxsplit=1)[split_idx].strip()
    def find_smi(self, n, block_size=None):
        with self as db:
            #TODO: add ability to stream line indices to avoid reading them into memory
            if n >= self._max_offset:
                self.create_line_index(n, return_index=False)
            db.seek(self._offsets[n])
            if block_size is None:
                self._cur = n
                return self._consume_next(db, split_idx=self.split_idx)
            else:
                self._cur = n + block_size
                if n + block_size >= self._max_offset:
                    blocks = []
                    for m in range(block_size):
                        if self._assignable_offsets:
                            self._expand_offset_if_needed(n+m)
                            self._offsets[n+m] = db.tell()
                        blocks.append(self._consume_next(db, split_idx=self.split_idx))
                    return blocks
                else:
                    return [
                        self._consume_next(db, split_idx=self.split_idx)
                        for _ in range(block_size)
                    ]
    def consume_iter(self, start_at=None, upto=None):
        with self as db:
            if start_at is None:
                start_at = self._cur
            ninds = start_at
            try:
                db.seek(self._offsets[ninds])
                if upto is None:
                    smi = self._consume_next(db, split_idx=self.split_idx)
                    while len(smi) > 0:
                        ninds += 1
                        if self._assignable_offsets:
                            self._expand_offset_if_needed(ninds)
                            self._offsets[ninds] = db.tell()
                        yield smi
                        smi = self._consume_next(db, split_idx=self.split_idx)
                else:
                    if ninds >= upto: return
                    smi = self._consume_next(db, split_idx=self.split_idx)
                    while ninds < upto and len(smi) > 0:
                        ninds += 1
                        if self._assignable_offsets:
                            self._expand_offset_if_needed(ninds)
                            self._offsets[ninds] = db.tell()
                        yield smi
                        smi = self._consume_next(db, split_idx=self.split_idx)
            finally:
                self._cur = ninds
                self._max_offset = max(self._max_offset, ninds)

    def __next__(self):
        if self._stream is None:
            cls = type(self)
            raise ValueError(f"{cls.__name__} must be opened via `with` before it can be iterated over")
        with self as db:
            db.seek(self._offsets[self._cur])
            return self._consume_next(db)

    def __iter__(self):
        return self.consume_iter()

    def _expand_offset_if_needed(self, n):
        if n >= len(self._offsets):
            if not self._flexible_offsets:
                raise ValueError(f"{self._max_offset} `line_indices` were passed, but db extends beyond that")
            else:
                new_offsets = np.zeros(2 * len(self._offsets), dtype='uint64')
                new_offsets[:len(self._offsets)] = self._offsets
                self._offsets = new_offsets
    def create_line_index(self, upto=None, return_index=True):
        with self as db:
            if not self._assignable_offsets:
                if return_index:
                    return self._offsets[:self._max_offset]
                else:
                    return None
            ninds = self._max_offset
            db.seek(self._offsets[ninds])
            try:
                if upto is None:
                    while len(db.readline()) > 0:
                        ninds += 1
                        self._expand_offset_if_needed(ninds)
                        self._offsets[ninds] = db.tell()
                else:
                    while ninds < upto and len(db.readline()) > 0:
                        ninds += 1
                        self._expand_offset_if_needed(ninds)
                        self._offsets[ninds] = db.tell()
            finally:
                self._max_offset = ninds
            if return_index:
                return self._offsets[:self._max_offset]
            else:
                return None
    @classmethod
    def save_line_index(cls, file, line_index):
        max_offset = line_index[-1]
        for dtype in [np.uint16, np.uint32, np.uint64]:
            if max_offset < np.iinfo(dtype).max:
                line_index = line_index.astype(dtype)
                break
        return np.save(file, line_index)

def _consume_supplier_mp(smiles_file, consumer, line_offset, block_size):
    offsets = np.full(block_size, line_offset)
    supplier = SMILESSupplier(smiles_file, line_indices=offsets)
    res = []
    with supplier:
        for smi in supplier.consume_iter(start_at=0, upto=block_size):
            subres = consumer(smi)
            if subres is not None: res.append(subres)
    return res

def consume_smiles_supplier(supplier:SMILESSupplier, consumer, pool=None, start_at=None, upto=None, initializer=None):
    if dev.is_int(pool):
        pool = multiprocessing.Pool(pool, initializer=initializer)

    if pool is None:
        res = []
        with supplier:
            for smi in supplier.consume_iter(start_at=start_at, upto=upto):
                subres = consumer(smi)
                if subres is not None: res.append(subres)

        return res
    else:
        with supplier:
            max_size = len(supplier) if upto is None else upto
            offsets = supplier._offsets # TODO: gross
            nproc = pool._processes
            block_size = max_size // nproc
            num_blocks = int(np.ceil(max_size / block_size))
            block_starts_sizes = [
                (offsets[block_size*i], min([block_size, max_size - (block_size*i+1) + 1]))
                for i in range(num_blocks)
            ]
            #TODO: don't access the `_input` argument directly...
            args = [(supplier.smi._input, consumer) + bs for bs in block_starts_sizes]
        res = pool.starmap(_consume_supplier_mp, args)

        return sum(res, [])

def _match_rdkit(matcher, smi):
    from rdkit.Chem import AllChem
    mol = AllChem.MolFromSmiles(smi)
    if mol is None: return None
    if mol.GetSubstructMatch(matcher): return smi

def _disable_rdkit_log(blockage=[]):
    from rdkit.rdBase import BlockLogs
    bl = BlockLogs()
    blockage.append([bl,  bl.__enter__()])

def match_smiles_supplier(supplier:SMILESSupplier, matcher, pool=None, start_at=None, upto=None, quiet=True,
                          initializer=None):
    from rdkit.rdBase import BlockLogs
    if isinstance(matcher, str):
        from .RDKit import RDKitInterface
        AllChem = RDKitInterface.submodule("Chem.AllChem")
        smarts_candidate = AllChem.MolFromSmarts(matcher)
        matcher = functools.partial(_match_rdkit, smarts_candidate)
        if quiet and initializer is None:
            initializer = _disable_rdkit_log
    if quiet:
        with BlockLogs():
            return consume_smiles_supplier(supplier, matcher, pool=pool, start_at=start_at, upto=upto, initializer=initializer)
    else:
        return consume_smiles_supplier(supplier, matcher, pool=pool, start_at=start_at, upto=upto, initializer=initializer)

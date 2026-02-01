from __future__ import annotations

import io
import os
import pathlib
import json
import tempfile
import tempfile as tf

from . import Options as opts_handler

__all__ = [
    "is_filepath_like",
    "safe_open",
    "write_file",
    "read_file",
    "read_json",
    "write_json",
    "split_path",
    "drop_directory_prefix",
    "FileBackedIO",
    "StreamInterface",
]

bad_file_chars = {" ", "\t", "\n"}
def is_filepath_like(file, bad_chars=None):
    if bad_chars is None:
        bad_chars = bad_file_chars
    return isinstance(file, pathlib.Path) or (
        isinstance(file, str)
        and all(b not in file for b in bad_chars)
    )

class safe_open:
    def __init__(self, file, **opts):
        self.file = file
        self._stream = None
        self.opts = opts
    def __enter__(self):
        if hasattr(self.file, 'seek'):
            return self.file
        else:
            self._stream = open(self.file, **self.opts)
            return self._stream.__enter__()
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._stream is not None:
            return self._stream.__exit__(exc_type, exc_val, exc_tb)

class open_opts:
    mode: 'str'
    buffering: 'int'
    encoding: 'str | None'
    errors: 'str | None'
    newline: 'str | None'
    closefd: 'bool'
    opener: '(str, int)'

def write_file(file, data, mode='w+', **opts):
    with safe_open(file, mode=mode, **opts) as fs:
        fs.write(data)
    return file

def read_file(file, **opts):
    with safe_open(file, **opts) as fs:
        return fs.read()

def read_json(file, **opts):
    opts, js_opts = opts_handler.OptionsSet(opts).split(open_opts)
    with safe_open(file, **opts) as fs:
        return json.load(fs, **js_opts)

def write_json(file, data, mode="w+", **opts):
    opts, js_opts = opts_handler.OptionsSet(opts).split(open_opts)
    with safe_open(file, mode=mode, **opts) as fs:
        return json.dump(data, fs)

def split_path(path, nsteps=-1):
    if len(path) == 0:
        return []

    if isinstance(path, pathlib.Path):
        splitter = lambda p:(p.parent,p.name)
    else:
        splitter = lambda p:(("","") if p == os.path.sep else os.path.split(p))
    if nsteps < 0:
        subpath = []
        root = path
        while len(root) > 0:
            root, end = splitter(root)
            subpath.append(end)
        return subpath[::-1]
    else:
        subpath = []
        root = path
        for i in range(nsteps):
            root, end = splitter(root)
            subpath.append(end)
            if len(root) == 0:
                break
        return [root] + subpath[::-1]

def drop_directory_prefix(prefix, path):
    split1 = split_path(prefix)
    split2 = split_path(path)
    i = -1
    for i,(s1,s2) in enumerate(zip(split1, split2)):
        if s1 != s2:
            break

    if i+1 < len(split2):
        subsplit = split2[i+1:]
        if subsplit[0] == "":
            subsplit[0] = os.path.sep
        subpath = os.path.join(*subsplit)
    else:
        subpath = ""

    if isinstance(path, pathlib.Path):
        subpath = pathlib.Path(subpath)
    return subpath

class FileBackedIO:
    def __init__(self, buffer:str|bytes, mode='w+', delete=True, **tempfile_opts):
        self.mode = mode
        self.opts = tempfile_opts
        self.buf = buffer
        self._file = None
        self._stream = None
        self.delete = delete

    @property
    def file(self):
        if self._file is None:
            if 'b' in self.mode:
                submode = 'w+b'
            else:
                submode = 'w+'
            with tempfile.NamedTemporaryFile(mode=submode, delete=False, **self.opts) as base:
                if 'w' not in self.mode:
                    base.write(self.buf)
            self._file = base.name
        return self._file

    def __enter__(self):
        if self._stream is None:
            self._stream = open(self.file, self.mode).__enter__()
            if 'w' in self.mode:
                self._stream.write(self.buf)
                self._stream.seek(0)
        return self._stream
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stream.__exit__(exc_type, exc_val, exc_tb)
        if self.delete:
            os.remove(self._file)


class StreamInterface:
    def __init__(self, stream, file_backed=False, **file_opts):
        self._input = stream
        self._io_wrapper = None
        self._stream = None
        self.file_backed = file_backed
        self.file_opts = file_opts
        self._was_open = None

    @classmethod
    def is_path_like(cls, input):
        return (len(input) > 0 and all(k not in input for k in ["\n", ",", "(", ")"]))

    def __enter__(self):
        if isinstance(self._input, str) and (os.path.exists(self._input) or self.is_path_like(self._input)):
            self._was_open = False
            self._io_wrapper = open(self._input, **self.file_opts)
            self._stream = self._io_wrapper.__enter__()
        elif isinstance(self._input, (str, bytes)):
            self._was_open = False
            if self.file_backed:
                self._io_wrapper = FileBackedIO(self._input, **self.file_opts)
            elif isinstance(self._input, str):
                self._io_wrapper = io.StringIO(self._input)
            else:
                self._io_wrapper = io.BytesIO(self._input)
            self._stream = self._io_wrapper.__enter__()
        else:
            self._was_open = True
            self._stream = self._input
        return self._stream

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._was_open is False:
            if self._io_wrapper is not None:
                try:
                    self._io_wrapper.__exit__(exc_type, exc_val, exc_tb)
                finally:
                    self._io_wrapper = None
            else:
                self._stream.__exit__(exc_type, exc_val, exc_tb)
            self._stream = None
            self._was_open = None
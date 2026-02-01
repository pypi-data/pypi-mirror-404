from __future__ import annotations

import enum
from mmap import mmap
import abc, io
import sys
import textwrap

__all__ = [
    "FileStreamReader",
    "FileStreamCheckPoint",
    "FileStreamerTag",
    "FileStreamReaderException",
    "StringStreamReader",
    "FileLineByLineReader",
    "StringLineByLineReader"
]

########################################################################################################################
#
#                                           FileStreamReader
#
class FileStreamCheckPoint:
    """
    A checkpoint for a file that can be returned to when parsing
    """
    def __init__(self, parent, revert = True):
        self.parent = parent
        self.chk = parent.tell()
        self._revert = revert
    def disable(self):
        self._revert = False
    def enable(self):
        self._revert = True
    def revert(self):
        self.parent.seek(self.chk)
    def __enter__(self, ):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._revert:
            self.revert()

class FileStreamReaderException(IOError):
    pass

class SearchStream(metaclass=abc.ABCMeta):
    """
    Represents a stream from which we can pull block of data.
    Just provides a core interface with which we can work
    """

    @abc.abstractmethod
    def read(self, n=-1):
        raise NotImplementedError("SearchStream is a base class")
    def rread(self, n=-1):
        cur = self.tell()
        if n > 0:
            if n > cur:
                targ = 0
                block = cur
            else:
                targ = cur - n
                block = n
        else:
            targ = 0
            block = cur
        self.seek(targ)
        res = self.read(block)
        self.seek(targ)
        return res
    @abc.abstractmethod
    def readline(self):
        raise NotImplementedError("SearchStream is a base class")
    @abc.abstractmethod
    def seek(self, *args, **kwargs):
        raise NotImplementedError("SearchStream is a base class")
    @abc.abstractmethod
    def tell(self):
        raise NotImplementedError("SearchStream is a base class")
    @abc.abstractmethod
    def find(self, tag, start=None, end=None):
        raise NotImplementedError("SearchStream is a base class")
    @abc.abstractmethod
    def rfind(self, tag, start=None, end=None):
        raise NotImplementedError("SearchStream is a base class")
    @abc.abstractmethod
    def tag_size(self, tag):
        raise NotImplementedError("SearchStream is a base class")

    @abc.abstractmethod
    def __iter__(self):
        ...
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class ByteSearchStream(SearchStream):
    """
    A stream that is implemented for searching in byte strings
    """
    def __init__(self, data, encoding="utf-8", **kw):
        """
        :param data:
        :type data: bytearray
        :param encoding:
        :type encoding:
        :param kw:
        :type kw:
        """
        self._data = data
        self._encoding = encoding
        self._kw = kw
        self._stream = None
        self._wasopen = None
    def __enter__(self):
        self._stream = io.BytesIO(self._data)
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stream.close()
    def __repr__(self):
        cls = type(self)
        stream = textwrap.shorten(repr(
            self._data
                if self._stream is None else
            self._stream
        ), 100)
        return f"{cls.__name__}({stream})"
    def __iter__(self):
        return iter(self._stream)
    def read(self, n=-1):
        return self._stream.read(n).decode(self._encoding)
    def readline(self):
        return self._stream.readline().decode(self._encoding)
    def seek(self, *args, **kwargs):
        return self._stream.seek(*args, **kwargs)
    def tell(self):
        return self._stream.tell()
    def encode_tag(self, tag):
        if not isinstance(tag, bytes):
            tag = tag.encode(self._encoding)
        return tag
    def find(self, tag, start=None, end=None):
        enc_tag = self.encode_tag(tag)
        if start is None:
            start = self.tell()
        if end is None:
            end = -1
        arg_vec = [enc_tag, start, end]
        return self._data.find(*arg_vec)
    def rfind(self, tag, start=None, end=None):
        enc_tag = self.encode_tag(tag)
        if start is None:
            start = 0
        if end is None:
            end = self.tell()
        arg_vec = [enc_tag, start, end]
        return self._data.rfind(*arg_vec)
    def tag_size(self, tag):
        enc_tag = self.encode_tag(tag)
        return len(enc_tag)

class FileSearchStream(SearchStream):
    """
    A stream that is implemented for searching in mmap-ed files
    """
    default_binary = True
    def __init__(self, file, mode="r", binary=None, encoding="utf-8",
                 check_decoding=False,
                 decoding_mode="strict",
                 **kw):
        self._file = file
        if binary is None:
            binary = self.default_binary
        if binary:
            mode = mode.strip("+b") + "+b"
        else:
            mode = mode.strip('+') + '+'
        self._mode = mode
        self._encoding = encoding
        self.check_decoding = check_decoding,
        self.decoding_mode = decoding_mode
        self._kw = kw
        self._stream = None
        self._wasopen = None
    def __repr__(self):
        cls = type(self)
        return f"{cls.__name__}({self._file}, {self._mode!r})"
    def __enter__(self):
        if isinstance(self._file, str):
            self._wasopen = False
            self._fstream = open(self._file, mode=self._mode, **self._kw)
        else:
            self._wasopen = True
            self._fstream = self._file
        self._stream = mmap(self._fstream.fileno(), 0)
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stream.close()
        if not self._wasopen:
            self._fstream.close()
    def __iter__(self):
        new_pos = self._stream.tell()
        not_exhausted = True
        while not_exhausted:
            line = self._stream.readline()
            old_pos = new_pos
            new_pos = self._stream.tell()
            not_exhausted = new_pos > old_pos
            if not_exhausted:
                yield line
    def handle_chunk(self, chunk):
        if isinstance(chunk, bytes):
            if self.check_decoding:
                try:
                    chunk = chunk.decode(self._encoding, self.decoding_mode)
                except UnicodeDecodeError:
                    raise ValueError(f"error decoding: {chunk}")
            else:
                chunk = chunk.decode(self._encoding, self.decoding_mode)
        return chunk
    def read(self, n=-1):
        return self.handle_chunk(self._stream.read(n))
    def readline(self):
        return self.handle_chunk(self._stream.readline())
    def seek(self, *args, **kwargs):
        return self._stream.seek(*args, **kwargs)
    def tell(self):
        return self._stream.tell()
    def find(self, tag, start=None, end=None):
        enc_tag = tag.encode(self._encoding)
        if start is None:
            start = self.tell()
        if end is None:
            end = -1
        arg_vec = [enc_tag, start, end]
        return self._stream.find(*arg_vec)
    def rfind(self, tag, start=None, end=None):
        enc_tag = tag.encode(self._encoding)
        if start is None:
            start = 0
        if end is None:
            end = self.tell()
        arg_vec = [enc_tag, start, end]

        return self._stream.rfind(*arg_vec)
    def tag_size(self, tag):
        enc_tag = tag.encode(self._encoding)
        return len(enc_tag)

class StringSearchStream(SearchStream):
    """
    A stream that is implemented for searching in strings.
    Current implementation creates a `StringIO` buffer to support `read`/`tell`/etc.
    This is very memory inefficient, but we're not winning performance awards for
    any of this anyway
    """
    def __init__(self, string):
        """
        :param string:
        :type string: str
        """
        self._data = string
        self._stream = None

    def __enter__(self):
        self._stream = io.StringIO(self._data)
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stream.close()
    def __iter__(self):
        return iter(self._stream)

    def read(self, n=-1):
        return self._stream.read(n)
    def readline(self):
        return self._stream.readline()
    def seek(self, *args, **kwargs):
        return self._stream.seek(*args, **kwargs)
    def tell(self):
        return self._stream.tell()
    def find(self, tag, start=None, end=None):
        if start is None:
            start = self.tell()
        if end is None:
            end = len(self._data) + 1
        arg_vec = [tag, start, end]

        return self._data.find(*arg_vec)
    def rfind(self, tag, start=None, end=None):
        if start is None:
            start = 0
        if end is None:
            end = self.tell()
        arg_vec = [tag, start, end]
        return self._data.rfind(*arg_vec)
    def tag_size(self, tag):
        return len(tag)

class SearchStreamReader:
    """
    Represents a reader which implements finding chunks of data in a stream
    """

    def __init__(self, stream):
        """
        :param stream:
        :type stream: SearchStream
        """
        self.stream = stream
        self._exhausted_tag_pos = {} # an optimization for tag alternative searching
        self._next_tag_pos = [{}, {}] # an optimization for tag alternative searching
    def __enter__(self):
        self.stream.__enter__()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stream.__exit__(exc_type, exc_val, exc_tb)
    def __repr__(self):
        cls = type(self)
        return f"{cls.__name__}({self.stream})"

    class StreamSearchDirection(enum.Enum):
        Forward = "forward"
        Reverse = "reverse"
        ForwardReverse = "forward-reverse"
        ReverseForward = "reverse-forward"

    @classmethod
    def _is_forward(self, direction):
        #TODO: optimize this away
        return self.StreamSearchDirection(direction) is self.StreamSearchDirection.Forward
    @classmethod
    def _is_reverse(self, direction):
        #TODO: optimize this away
        return self.StreamSearchDirection(direction) is self.StreamSearchDirection.Reverse

    def _find_tag(self, tag,
                  skip_tag=True,
                  seek=True,
                  direction='forward'
                  ):
        """
        Finds a tag in a file

        :param header: a tag specifying a header to look for + optional follow-up processing/offsets
        :type header: FileStreamerTag
        :return: position of tag
        :rtype: int
        """
        direction = self.StreamSearchDirection(direction)
        forward = self._is_forward(direction)
        with FileStreamCheckPoint(self, revert=False) as chk:
            if forward:
                pos = self.stream.find(tag)
            else:
                pos = self.stream.rfind(tag)

            if pos >= 0:
                if skip_tag:
                    tag_size = self.stream.tag_size(tag)
                else:
                    tag_size = 0
                pos += tag_size
                if seek:
                    self.stream.seek(pos)
            elif pos < 0:
                chk.revert()
        return pos

    def find_tag(self,
                 tag,
                 skip_tag=None,
                 seek=None,
                 allow_terminal=False,
                 validator=None,
                 return_body=False,
                 direction='forward'
                 ):
        """
        Finds a tag in a file

        :param header: a tag specifying a header to look for + optional follow-up processing/offsets
        :type header: FileStreamerTag
        :return: position of tag
        :rtype: int
        """
        if isinstance(tag, str):
            tags = FileStreamerTag(tag)
        elif isinstance(tag, dict):
            tag = tag.copy()
            t = tag['tag']
            del tag['tag']
            tags = FileStreamerTag(t, **tag)
        else:
            tags = tag

        pos = -1
        if skip_tag is None:
            skip_tag = tags.skip_tag
        if seek is None:
            seek = tags.seek
        res = None

        tag_positions = {}
        cur = self.tell()
        tag = None
        direction = self.StreamSearchDirection(direction)
        forward = self._is_forward(direction)
        reverse = not forward
        for t in tags.tags:
            # if (
            #         t not in self._exhausted_tag_pos
            #         or cur < self._exhausted_tag_pos[t]
            # ):
            #     self.seek(cur)
            #     pos = self._find_tag(t, skip_tag=skip_tag, seek=seek)
            #     if pos < 0:
            #         self._exhausted_tag_pos[t] = cur
            #     else:
            #         tag_positions[pos] = t

            if forward:
                (cur_test, p_test) = self._next_tag_pos[0].get(t, (cur + 1, -1))
                if (
                        (p_test < 0 or p_test >= cur_test)
                        and cur_test <= cur and p_test >= cur
                ):
                    if p_test > 0:
                        tag_positions[p_test] = t
                    continue
            else:
                (cur_test, p_test) = self._next_tag_pos[1].get(t, (cur-1, -1))
                if (
                        (p_test < 0 or p_test <= cur_test)
                        and cur_test >= cur and p_test <= cur
                ):
                    if p_test >= 0:
                        tag_positions[p_test] = t
                    continue

            self.seek(cur)
            pos = self._find_tag(t, skip_tag=skip_tag, seek=seek, direction=direction)
            if forward:
                self._next_tag_pos[0][t] = (cur, pos)
            else:
                self._next_tag_pos[1][t] = (cur, pos)
            if pos > 0:
                tag_positions[pos] = t

        tag_keys = sorted(tag_positions.keys())
        if reverse:
            tag_keys = reversed(tag_keys)
        for pos in tag_keys:
            og_pos = pos
            tag = tag_positions[pos]
            if skip_tag and (return_body or validator is not None):
                ts = self.stream.tag_size(tag)
            else:
                ts = 0

            follow_ups = tags.skips
            if follow_ups is not None:
                for tag in follow_ups:
                    if not skip_tag:
                        if forward:
                            self.stream.seek(pos+1)
                        else:
                            self.stream.seek(pos-1)
                    else:
                        self.stream.seek(pos)
                    p = self.find_tag(tag, seek=False, direction=direction)
                    if allow_terminal or p > -1:
                        pos = p
                if not seek:
                    self.seek()
                if validator is not None:
                    block_size = abs(pos - og_pos + ts)
                    if forward:
                        self.stream.seek(og_pos - ts)
                        res = self.stream.read(block_size)
                    else:
                        self.stream.seek(pos + ts)
                        res = self.stream.rread(block_size)
                    test = validator(res)
                    if test == self.TagSentinels.NextMatch:
                        return self.find_tag(tags,
                                             skip_tag=skip_tag,
                                             seek=seek,
                                             allow_terminal=allow_terminal,
                                             validator=validator,
                                             return_body=return_body
                                             )
                    while test == self.TagSentinels.Continue or not test:
                        if forward:
                            self.stream.seek(pos + 1)
                        else:
                            self.stream.seek(pos - 1)
                        p = self.find_tag(tag, direction=direction)
                        pos = p
                        if p == -1:
                            break
                        else:
                            block_size = abs(pos - og_pos + ts)
                            if forward:
                                self.stream.seek(og_pos - ts)
                                res = self.stream.read(block_size)
                            else:
                                self.stream.seek(pos + ts)
                                res = self.stream.rread(block_size)
                            test = validator(res)
                            if test == self.TagSentinels.NextMatch:
                                return self.find_tag(tags,
                                                     skip_tag=skip_tag,
                                                     seek=seek,
                                                     allow_terminal=allow_terminal,
                                                     validator=validator,
                                                     return_body=return_body,
                                                     direction=direction
                                                     )
                    if pos < 0:
                        res = None
                        continue
                else:
                    block_size = abs(pos - og_pos + ts)
                    if forward:
                        self.stream.seek(og_pos - ts)
                        res = self.stream.read(block_size)
                    else:
                        self.stream.seek(pos + ts)
                        res = self.stream.rread(block_size)

            else:
                block_size = abs(pos - og_pos + ts)
                if forward:
                    self.stream.seek(og_pos - ts)
                    res = self.stream.read(block_size)
                else:
                    self.stream.seek(pos + ts)
                    res = self.stream.rread(block_size)

            offset = tags.offset
            if offset is not None:
                # why are we using self._stream.tell here...?
                # I won't touch it for now but I feel like it should be pos
                if forward:
                    pos = self.stream.tell() + offset
                else:
                    pos = self.stream.tell() - offset

            if return_body and res is None:
                if forward:
                    self.stream.seek(og_pos - ts)
                    res = self.stream.read(pos - og_pos + ts)
                else:
                    self.stream.seek(pos)
                    res = self.stream.rread(abs(pos - og_pos - ts))
            if not skip_tag:
                if forward:
                    self.stream.seek(og_pos)
                else:
                    self.stream.seek(pos + ts)
                pos = og_pos
            break # first match in alternatives

        if seek is False:
            self.seek(cur)

        if return_body:
            return res, pos
        else:
            return pos

    class TagSentinels(enum.Enum):
        EOF = 'end_of_file'
        Continue = "continue"
        NextMatch = "next_match"
    def _parse_end_block(self,
                         start, tag_end, allow_terminal,
                         expand_until_valid, validator,
                         direction="forward"
                         ):
        with FileStreamCheckPoint(self):
            end = self.find_tag(tag_end, allow_terminal=allow_terminal, seek=False, direction=direction)
        reverse = self._is_reverse(direction)
        forward = not reverse
        if reverse:
            start, end = end, start
        if (start < 0 or end < 0):
            if allow_terminal:
                block = self.stream.read()
                if not validator(block):
                    block = None
            else:
                block = self.TagSentinels.EOF
        else:
            if forward:
                block = self.stream.read(end - start)
            else:
                block = self.stream.rread(end - start)

            if expand_until_valid:
                with FileStreamCheckPoint(self) as chk:
                    if not validator(block):
                        if forward:
                            block = block + self.stream.read(1)
                        else:
                            block = self.stream.rread(1) + block
                    while not validator(block):
                        if forward:
                            self.stream.seek(end + 1)
                            extra = self.find_tag(tag_end, allow_terminal=allow_terminal, seek=False, direction=direction)
                            if extra > 0:
                                block = block + self.stream.read(extra - end)
                                end = extra
                            else:
                                if allow_terminal:
                                    self.stream.seek(start)
                                    block = self.stream.read()
                                    if not validator(block):
                                        block = None
                                    end = -1
                                else:
                                    block = None
                                break
                        else:
                            self.stream.seek(max(start - 1, 0))
                            extra = self.find_tag(tag_end, allow_terminal=allow_terminal, seek=False, direction=direction)
                            if extra > 0:
                                block = self.stream.rread(start - extra) + block
                                start = extra
                            else:
                                if allow_terminal:
                                    self.stream.seek(end)
                                    block = self.stream.rread()
                                    if not validator(block):
                                        block = None
                                    start = -1
                                else:
                                    block = None
                                break
                    if block is not None:
                        chk.disable()
        return (start, end), block

    @classmethod
    def _get_search_directions(cls, direction):
        direction = cls.StreamSearchDirection(direction)
        if direction is cls.StreamSearchDirection.Forward:
            start_direction = end_direction = cls.StreamSearchDirection.Forward
        elif direction is cls.StreamSearchDirection.Reverse:
            start_direction = end_direction = cls.StreamSearchDirection.Reverse
        elif direction is cls.StreamSearchDirection.ForwardReverse:
            start_direction, end_direction = cls.StreamSearchDirection.Forward, cls.StreamSearchDirection.Reverse
        else:
            start_direction, end_direction = cls.StreamSearchDirection.Reverse, cls.StreamSearchDirection.Forward
        return start_direction, end_direction
    def get_tagged_block(self, tag_start, tag_end,
                         validator=None, tag_validator=None,
                         allow_terminal=False,
                         expand_until_valid=False,
                         return_tag=False,
                         return_end_points=False,
                         direction='forward',
                         block_size=500):
        """
        Pulls the string between tag_start and tag_end

        :param tag_start:
        :type tag_start: FileStreamerTag or None
        :param tag_end:
        :type tag_end: FileStreamerTag
        :return:
        :rtype:
        """

        block = None
        tag_body = None
        end_points = None

        start_direction, end_direction = self._get_search_directions(direction)
        _eps = end_points
        while block is None:
            if tag_start is not None:
                tag_str, start = self.find_tag(tag_start,
                                               allow_terminal=False,
                                               return_body=True,
                                               validator=tag_validator,
                                               direction=start_direction)

                if start >= 0:
                    end_points, block = self._parse_end_block(start, tag_end, allow_terminal, expand_until_valid,
                                                              validator, end_direction)
                    if end_points is not None and _eps is not None and end_points == _eps:
                        raise ValueError(f"stuck in a loop while searching for {tag_end} starting from {start} in dir {end_direction}")
                    _eps = end_points
                    if block is not None:
                        tag_body = tag_str
                else:
                    block = self.TagSentinels.EOF
                    end_points = (start,-1)
            else:
                start = self.tell()
                end_points, block = self._parse_end_block(start, tag_end, allow_terminal, expand_until_valid,
                                                          validator, end_direction)

            if (
                    not expand_until_valid
                    and block is not None
                    and block is not self.TagSentinels.EOF
                    and (validator is not None and not validator(block))
            ):
                block = None
                if self._is_forward(start_direction):
                    self.seek(end_points[-1]+1)
                else:
                    self.seek(end_points[0]-1)
                end_points = None

        if block is self.TagSentinels.EOF:
            block = None

        if return_tag or return_end_points:
            aux = ()
            if return_tag:
                aux = aux + (tag_body,)
            if return_end_points:
                aux = aux + (end_points,)
            return aux, block
        else:
            return block

    def _parse_block(self, tag_start, tag_end, validator, tag_validator,
                     allow_terminal, expand_until_valid, preserve_tag, return_end_points, direction):
        ret_tag = preserve_tag
        if ret_tag and isinstance(tag_start, FileStreamerTag):
            ret_tag = tag_start.skip_tag
        block = self.get_tagged_block(tag_start, tag_end,
                                      validator=validator,
                                      tag_validator=tag_validator,
                                      return_tag=ret_tag,
                                      return_end_points=return_end_points,
                                      allow_terminal=allow_terminal,
                                      expand_until_valid=expand_until_valid,
                                      direction=direction
                                      )

        end_points = None
        if ret_tag:
            start_direction, end_direction = self._get_search_directions(direction)
            if return_end_points:
                (tag_body, end_points), block = block
            else:
                (tag_body,), block = block
            if self._is_forward(end_direction) and block is not None and tag_body is not None:
                block = tag_body + block
                if end_points is not None:
                    start, end = end_points
                    if self._is_forward(start_direction):
                        start = start - len(tag_body)
                    end_points = (start, end)
        elif return_end_points:
            (end_points,), block = block

        if end_points is not None:
            return end_points, block
        else:
            return block
    def parse_key_block(self,
                        tag_start=None,
                        tag_end=None,
                        mode="Single",
                        validator=None,
                        tag_validator=None,
                        expand_until_valid=False,
                        preserve_tag=False,
                        return_end_points=False,
                        parser=None,
                        parse_mode="List",
                        num=None,
                        pass_context=False,
                        allow_terminal=False,
                        direction="forward",
                        **ignore
                        ):
        """Parses a block by starting at tag_start and looking for tag_end and parsing what's in between them

        :param key: registered key pattern to pull from a file
        :type key: str
        :return:
        :rtype:
        """
        # if tag_start is None:
        #     raise FileStreamReaderException("{}.{}: needs a '{}' argument".format(
        #         type(self).__name__,
        #         "parse_key_block",
        #         "tag_start"
        #     ))
        if tag_end is None:
            raise FileStreamReaderException("{}.{}: needs a '{}' argument".format(
                type(self).__name__,
                "parse_key_block",
                "tag_end"
            ))
        if mode == "List":
            with FileStreamCheckPoint(self):
                # we do this in a checkpointed fashion only for list-type tokens
                # for all other tokens we introduce an ordering to apply when checking
                # does it need to be done like this... probably not?
                # I suppose we could be a significantly more efficient by returning a
                # generator statement in these multi-block cases
                # and then introducing a sorting order across these multi-blocks
                # that tells us which to check first, second, etc.
                # but this is probably good enough
                if isinstance(num, int):
                    blocks = [None]*num
                    if parser is None:
                        parser = lambda a, reader=None:a

                    i = 0 # protective
                    for i in range(num):
                        block = self._parse_block(tag_start, tag_end, validator, tag_validator,
                                                  allow_terminal, expand_until_valid, preserve_tag, return_end_points,
                                                  direction)
                        if block is None:
                            break
                        if parse_mode != "List":
                            if pass_context:
                                block = parser(block, reader=self)
                            else:
                                block = parser(block)
                        blocks[i] = block

                    if parse_mode == "List":
                        blocks = parser(blocks[:i+1])
                else:
                    blocks = []
                    block = self._parse_block(tag_start, tag_end, validator, tag_validator,
                                              allow_terminal, expand_until_valid, preserve_tag, return_end_points,
                                              direction)
                    if parser is None:
                        parser = lambda a, reader=None:a
                    while block is not None:
                        if parse_mode != "List":
                            if pass_context:
                                block = parser(block, reader=self)
                            else:
                                block = parser(block)

                        blocks.append(block)
                        block = self._parse_block(tag_start, tag_end, validator, tag_validator,
                                                  allow_terminal, expand_until_valid, preserve_tag, return_end_points,
                                                  direction)

                    if parse_mode == "List":
                        if pass_context:
                            blocks = parser(blocks, reader=self)
                        else:
                            blocks = parser(blocks)
                return blocks
        else:
            block = self._parse_block(tag_start, tag_end, validator, tag_validator,
                                      allow_terminal, expand_until_valid, preserve_tag, return_end_points,
                                      direction)
            if parser is not None:
                block = parser(block)
            return block

    def read(self, n=1):
        return self.stream.read(n)
    def readline(self):
        return self.stream.readline()
    def seek(self, *args, **kwargs):
        return self.stream.seek(*args, **kwargs)
    def tell(self):
        return self.stream.tell()
    def find(self, tag):
        return self.stream.find(tag)
    def rfind(self, tag, search_window=None):
        if hasattr(self.stream, 'rfind'):
            return self.stream.rfind(tag)
        else:
            cur = self.stream.tell()
            if search_window is None:
                start = 0
            else:
                start = cur - search_window
            self.seek(start)
            body = self.read(cur)
            pos = body.rfind(tag)
            if pos > 0:
                pos = start + pos
            return pos
    def skip_tag(self, tag):
        return self.stream.skip_tag(tag)
    def rskip_tag(self, tag):
        return self.stream.rskip_tag(tag)

class FileStreamReader(SearchStreamReader):
    """
    Represents a file from which we'll stream blocks of data by finding tags and parsing what's between them
    """
    def __init__(self, file, mode="r", encoding="utf-8", **kw):
        stream = FileSearchStream(file, mode=mode, encoding=encoding, **kw)
        super().__init__(stream)
class StringStreamReader(SearchStreamReader):
    """
    Represents a string from which we'll stream blocks of data by finding tags and parsing what's between them
    """
    def __init__(self, string):
        stream = StringSearchStream(string)
        super().__init__(stream)
class ByteStreamReader(SearchStreamReader):
    """
    Represents a string from which we'll stream blocks of data by finding tags and parsing what's between them
    """
    def __init__(self, string, encoding="utf-8", **kw):
        stream = ByteSearchStream(string, encoding=encoding, **kw)
        super().__init__(stream)

class FileStreamerTag:
    def __init__(self,
                 tag_alternatives=None,
                 follow_ups=None,
                 offset=None,
                 direction="forward",
                 skip_tag=True,
                 seek=True
                 ):
        if tag_alternatives is None:
            raise FileStreamReaderException("{} needs to be supplied with some set of tag_alternatives to look for".format(
                type(self).__name__
            ))
        self.tags = (tag_alternatives,) if isinstance(tag_alternatives, str) else tag_alternatives
        self.skips = (follow_ups,) if isinstance(follow_ups, (str, FileStreamerTag)) else follow_ups
        self.offset = offset
        self.direction = direction
        self.skip_tag = skip_tag
        self.seek = seek

    def __repr__(self):
        cls = type(self)
        return f"{cls.__name__}({self.tags=}, {self.skip_tag=}, {self.seek=})"

class LineByLineParser(metaclass=abc.ABCMeta):
    def __init__(self, stream, binary=True, encoding='utf-8', max_nesting_depth=-1, ignore_comments=False):
        """
        :param stream:
        :type stream: SearchStream
        """
        self.stream = stream
        self.binary = binary
        self.encoding = encoding
        self.max_nesting_depth = max_nesting_depth
        self.ignore_comments = ignore_comments

    def __enter__(self):
        self.stream.__enter__()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stream.__exit__(exc_type, exc_val, exc_tb)
    @abc.abstractmethod
    def check_tag(self, line, depth:int=0, active_tag=None, label:str=None, history:list[str]=None):
        ...
    def handle_block_line(self, label, line, depth=0, history:list[str]=None):
        return line
    def handle_block(self, label, block, depth=0):
        return block
    class LineReaderTags(enum.Enum):
        RESETTING_BLOCK_END = 'implict_end'
        BLOCK_END = 'end'
        BLOCK_START = 'block'
        COMMENT = "comment"
        SKIP = "skip"
        VALUE = "value"
    def read_stream_line(self, binary=None):
        if binary is None:
            binary = self.binary
        data = next(iter(self.stream))
        if not binary and hasattr(data, 'decode'):
            data = data.decode(self.encoding)
        return data
    def stream_iter(self, binary=None):
        if binary is None:
            binary = self.binary
        line_iter = iter(self.stream)
        try:
            data = next(line_iter)
        except StopIteration:
            yield None
        test = not binary and hasattr(data, 'decode')
        if test:
            data = data.decode(self.encoding)
        yield data
        if test:
            for data in line_iter:
                data = data.decode(self.encoding)
                yield data
        else:
            for line in line_iter:
                yield line

    def find_next_block(self, binary=None, ignore_comments=None, max_nesting_depth=None,
                        aggregate_values=True, depth=0):
        if ignore_comments is None:
            ignore_comments = self.ignore_comments
        if max_nesting_depth is None:
            max_nesting_depth = self.max_nesting_depth

        stream_pos = self.stream.tell()
        block_data = []
        empty = True
        active_tag = None
        label = None
        try:
            for i,line in enumerate(self.stream_iter(binary=binary)):
                if line is None: break
                empty = False
                next_tag = self.check_tag(line, depth, active_tag=active_tag, label=label, history=block_data)
                tag_label = tag_body = None
                if not isinstance(next_tag, self.LineReaderTags) and next_tag is not None:
                    if isinstance(next_tag, (str, bytes)):
                        tag_label = next_tag
                        next_tag = None
                    elif len(next_tag) == 2:
                        next_tag, tag_body = next_tag
                    else:
                        next_tag, tag_label, tag_body = next_tag
                if next_tag == self.LineReaderTags.SKIP:
                    stream_pos = self.stream.tell()
                    continue
                if ignore_comments and next_tag == self.LineReaderTags.COMMENT:
                    stream_pos = self.stream.tell()
                    continue
                if next_tag is self.LineReaderTags.VALUE:
                    if not aggregate_values:
                        next_tag = self.LineReaderTags.BLOCK_START
                    else:
                        if tag_label is not None:
                            val = self.handle_block_line(tag_label, line, depth)
                        elif tag_body is None:
                            raise ValueError("got {} tag but no associated `(key,value)` pair")
                        else:
                            val = self.handle_block_line(label, line, depth)
                        block_data.append(val)
                        stream_pos = self.stream.tell()
                        continue

                if next_tag is self.LineReaderTags.BLOCK_END:
                    if tag_body is not None: block_data.append(tag_body)
                    stream_pos = None
                    break
                elif next_tag is self.LineReaderTags.BLOCK_START:
                    if active_tag is None:
                        label = tag_label
                        if tag_body is not None: block_data.append(tag_body)
                    else:
                        if max_nesting_depth < 0 or depth < max_nesting_depth:
                            self.stream.seek(stream_pos)
                            sub_block = self.find_next_block(binary=binary, ignore_comments=ignore_comments,
                                                             max_nesting_depth=max_nesting_depth, depth=depth+1)
                            block_data.append(sub_block)
                        else:
                            break
                elif next_tag is self.LineReaderTags.RESETTING_BLOCK_END:
                    break
                elif active_tag is not None and next_tag is not None and next_tag != active_tag:
                    if depth == 0 or (max_nesting_depth > 0 and depth >= max_nesting_depth):
                        break
                    else:
                        self.stream.seek(stream_pos)
                        sub_block = self.find_next_block(binary=binary, ignore_comments=ignore_comments,
                                                         max_nesting_depth=max_nesting_depth, depth=depth + 1)
                        block_data.append(sub_block)
                else:
                    if tag_body is not None: block_data.append(tag_body)
                    if next_tag is not None and active_tag is None:
                        active_tag = next_tag
                        stream_pos = None
                        break
                    block_data.append(self.handle_block_line(label, line, depth))
                stream_pos = self.stream.tell()
                if active_tag is None and next_tag is not None:
                    active_tag = next_tag
        except StopIteration:
            pass
        finally:
            if stream_pos is not None:
                self.stream.seek(stream_pos)

        if empty:
            return None
        else:
            if label is None:
                return self.handle_block(None, block_data)
            else:
                return {label:self.handle_block(label, block_data)}

    MAX_BLOCKS = sys.maxsize # a debug tool
    def __iter__(self):
        block = self.find_next_block()
        for i in range(self.MAX_BLOCKS):
            if block is None: break
            yield block
            block = self.find_next_block()

class FileLineByLineReader(LineByLineParser):
    """
    Represents a file from which we'll stream blocks of data by finding tags and parsing what's between them
    """
    def __init__(self, file,
                 mode="r", binary=False, encoding="utf-8",
                 ignore_comments=False, max_nesting_depth=-1, **kw):
        stream = FileSearchStream(file, binary=binary, mode=mode, encoding=encoding, **kw)
        super().__init__(stream,
                         binary='b' in stream._mode, encoding=encoding,
                         ignore_comments=ignore_comments, max_nesting_depth=max_nesting_depth
                         )
class StringLineByLineReader(LineByLineParser):
    """
    Represents a string from which we'll stream blocks of data by finding tags and parsing what's between them
    """
    def __init__(self, string, ignore_comments=False, max_nesting_depth=-1):
        stream = StringSearchStream(string)
        super().__init__(stream, binary=False, ignore_comments=ignore_comments, max_nesting_depth=max_nesting_depth)
class ByteLineByLineReader(LineByLineParser):
    """
    Represents a string from which we'll stream blocks of data by finding tags and parsing what's between them
    """
    def __init__(self, string, encoding="utf-8", ignore_comments=False, max_nesting_depth=-1, **kw):
        stream = ByteSearchStream(string, encoding=encoding, **kw)
        super().__init__(stream, binary=True, encoding=encoding,
                         ignore_comments=ignore_comments,
                         max_nesting_depth=max_nesting_depth)

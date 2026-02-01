from __future__ import annotations

import abc, numpy as np, io, weakref
import collections
import os
import functools
import re
import shutil
import tempfile as tf
import itertools
from cProfile import label

from setuptools.command.easy_install import auto_chmod

from .. import Devutils as dev
from .. import Numputils as nput
from .. import Parsers
from .TableFormatters import TableFormatter
from ..Misc.Symbolics import Abstract

__all__ = [
    "TeX",
    "TeXTranspiler"
]

class TeXWriter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def format_tex(self, context=None):
        ...

    real_digits = 3
    @classmethod
    def dispatch_format(cls, b, context):
        if isinstance(b, TeXWriter) or hasattr(b, 'format_tex'):
            return b.format_tex(context)
        elif isinstance(b, (float, np.floating)):
            return ('{:.'+str(cls.real_digits)+'f}').format(b)
        elif isinstance(b, np.ndarray):
            return TeXArray(b).format_tex(context)
        elif isinstance(b, (list, tuple)):
            if isinstance(b[0], (list, tuple)):
                return TeXArray(b).format_tex(context)
            else:
                return TeXRow(b).format_tex(context)
        else:
            return str(b)

    def as_expr(self):
        return TeXExpr(self)

class TeXContextManager:
    default_contexts = weakref.WeakValueDictionary()
    @classmethod
    def resolve(cls, name='default'):
        if name not in cls.default_contexts:
            ctx = cls()
            cls.default_contexts[name] = ctx
        return cls.default_contexts[name]

    def __init__(self):
        self.context_stack = []
    def subcontext(self, cls):
        return cls(self)
    def set_context(self, ctx):
        self.context_stack.append(ctx)
        return ctx
    def leave_context(self):
        self.context_stack.pop()
    @property
    def context(self):
        if len(self.context_stack) == 0:
            return None
        else:
            return self.context_stack[-1]
    @property
    def math_mode(self):
        return isinstance(self.context, MathContext)

class TeXContext:
    def __init__(self, manager:TeXContextManager):
        self.manager = manager
    def __enter__(self):
        self.manager.set_context(self)
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.leave_context()
class MathContext(TeXContext):
    ...

class TeXBlock(TeXWriter):
    tag = None
    modifier = None
    modifier_type = '[]'
    separator = '\n'
    context = None
    label_header = None
    def __init__(self,
                 body=None, *,
                 tag=None,
                 modifier=None,
                 modifier_type=None,
                 separator=None,
                 context=None,
                 label=None
                 ):
        self.body = body
        if tag is None:
            tag = self.tag
        self.tag = tag
        if modifier is None:
            modifier = self.modifier
        self.modifier = modifier
        if modifier_type is None:
            modifier_type = self.modifier_type
        self.modifier_type = modifier_type
        if separator is None:
            separator = self.separator
        self.sep = separator
        if context is None:
            context = self.context
        self.ctx = context
        self.label = label
    def prep_body(self, context=None):
        if self.body is None:
            params = []
        elif isinstance(self.body, (list, tuple)):
            params = [self.dispatch_format(b, context) for b in self.body]
        else:
            params = [self.dispatch_format(self.body, context)]
        if self.label is not None:
            label = self.label
            if self.label_header is not None and ':' not in label:
                label = self.label_header + ':' + label
            params = params + ['\\label{' + label + "}"]
        return params
    @classmethod
    def construct_modified_tag(self, tag, mod, mod_type='[]'):
        header = "\\begin{"+str(tag)+"}"
        if mod is not None:
            if isinstance(mod_type, str):
                l, r = mod_type
                header = header + l + mod + r
            else:
                bits = []
                for m,t in zip(mod, mod_type):
                    l, r = t
                    bits.append(l + m + r)
                header = header + "".join(bits)
        return header, "\\end{"+str(tag)+"}"
    def construct_header_footer(self):
        return self.construct_modified_tag(self.tag, self.modifier, self.modifier_type)
    def format_body(self, body_params):
        header, footer = self.construct_header_footer()
        if self.tag is not None:
            body_params = [header] + body_params + [footer]
        return self.sep.join(body_params)
    def format_tex(self, context=None):
        if self.ctx is not None:
            if context is None:
                context = TeXContextManager.resolve()
            elif isinstance(context, str):
                context = TeXContextManager.resolve(context)

        if self.ctx is not None:
            with context.subcontext(self.ctx):
                body_args = self.prep_body(context)
        else:
            body_args = self.prep_body(context)
        return self.format_body(body_args)
    def __call__(self, body):
        return type(self)(
            body,
            tag=self.tag,
            modifier=self.modifier,
            modifier_type=self.modifier_type,
            separator=self.separator,
            context=self.ctx,
            label=self.label
        )

class TeXRow(TeXBlock):
    tag = None
    separator = ' '

class TeXArray(TeXBlock):
    tag = 'tabular'
    modifier_type = '{}'
    separator = '\n'
    array_separator = " & "
    array_newline = " \\\\\n"
    header_separator = "\n\\hline \\\\[-4ex]\n"
    header_lines = "\n\\hline \\\\[-4ex]"
    footer_lines = "\\hline \\\\[-4ex]\n"
    number_format = "{:8.3f}"
    def __init__(self, headers_or_body, body=None, *,
                 alignment='auto',
                 number_format="{:8.3f}",
                 content_join=None,
                 column_join=None,
                 row_join=None,
                 separator=None,
                 header_spans=None,
                 header_alignments=None,
                 resizeable=False,
                 **opts):
        self.resizeable = resizeable
        if resizeable:
            self.tag = 'tabularx'
            self.modifier_type = ["{}", "{}"]
            self.array_separator = " && "

        if body is None:
            body = headers_or_body
            headers_or_body = None
        self.headers = headers_or_body
        self.alignment = alignment
        if content_join is None:
            content_join = self.header_separator
        opts['content_join'] = content_join
        if row_join is None:
            row_join = self.array_newline
        opts['row_join'] = row_join
        if column_join is None:
            column_join = self.array_separator
        opts['column_join'] = column_join
        if separator is None:
            separator = ""
        opts['separator'] = separator
        self.format_opts, opts = dev.OptionsSet(opts).split(TableFormatter)
        self.format = number_format
        self.header_spans = header_spans
        self.header_alignments = header_alignments
        super().__init__(
            body,
            **opts
        )

    def construct_alignment_spec(self, body):
        if isinstance(body, np.ndarray):
            if np.issubdtype(body.dtype, np.integer):
                spec = "c" * body.shape[1]
            elif np.issubdtype(body.dtype, np.floating):
                spec = 'r' * body.shape[1]
            else:
                spec = 'c' * body.shape[1]
        else:
            specs = []
            for array_row in body:
                for i, e in enumerate(array_row):
                    if i >= len(specs):
                        specs = specs + ['r']
                    if (
                            specs[i] != 'c' and
                            not isinstance(e, (float, np.floating)) and
                            not (isinstance(e, str) and len(e.strip()) == 0)
                    ):
                        specs[i] = 'c'
            spec = "".join(specs)
        return spec
    def construct_header_footer(self):
        body = self.body
        if isinstance(body, np.ndarray) and not np.issubdtype(body.dtype, (np.integer, np.floating)):
            body = body.tolist()
        if self.alignment is not None and self.modifier is None:
            mod = self.construct_alignment_spec(body)
        else:
            mod = self.modifier
        if self.resizeable:
            mod = ['\\textwidth', "X".join(mod)]
        header, footer = self.construct_modified_tag(self.tag, mod, self.modifier_type)
        return header + self.header_lines, self.footer_lines + footer

    def format_numpy_array(self, array):
        int_digits = int(np.floor(np.log10(np.max(np.abs(array))))) + 1
        with io.StringIO() as stream:
            if np.issubdtype(array.dtype, np.floating):
                real_digits = self.real_digits
            else:
                real_digits = 0
            total_digits = int_digits + real_digits + 2
            fmt = '%{}.{}f'.format(total_digits, real_digits)
            np.savetxt(stream, array, fmt=fmt, delimiter=self.array_separator, newline=self.array_newline)
            stream.seek(0)
            return stream.read()
    def format_mixed_array(self, array, context=None):
        row_padding = []
        string_array = []
        for array_row in array: # convert and track padding
            conv_row = []
            for i,c in enumerate(array_row):
                s = self.dispatch_format(c, context)
                conv_row.append(s)
                if i >= len(row_padding):
                    row_padding = row_padding + [0]
                if len(s) > row_padding[i]:
                    row_padding[i] = len(s)
            string_array.append(conv_row)
        return self.array_newline.join(
            self.array_separator.join(" " * (row_padding[i] - len(s)) + s for i,s in enumerate(string_row))
            for string_row in string_array
        )
    def prep_body(self, context=None, headers=None, body=None):
        if body is None:
            body = self.body
        if headers is None:
            headers = self.headers
        if headers is None:
            if len(body) == 2 and not all(dev.is_atomic(b) for b in body[0]):
                headers, body = body
        opts = self.format_opts
        if 'column_formats' in opts:
            opts = opts.copy()
            column_formats = opts.pop('column_formats')
        else:
            column_formats = [
                ""
                    if not nput.is_numeric(o) else
                "{:>.0f}"
                    if nput.is_int(o) else
                self.format
                for o in body[0]
            ]

        if headers is not None:
            if dev.is_list_like(headers[0]):
                headers = [
                    [
                        h.format_tex(context=context)
                        if isinstance(h, TeXWriter) else
                        h
                        for h in hl
                    ]
                    for hl in headers
                ]
                if self.header_spans is not None:
                    alignments = self.header_alignments
                    if alignments is None:
                        alignments = [
                            ["c"] * len(hl)
                            for hl in headers
                        ]

                    _blocks = []
                    for lhl, lhs, lhc in zip(headers, self.header_spans, alignments):
                        _ = []
                        for hl, hs, hc in zip(lhl, lhs, lhc):
                            _.append(
                                TeXMulticolumn(2*hs - 1, hc, hl).format_tex(context)
                                    if hs > 1 else
                                hl
                            )
                        _blocks.append(_)
                    headers = _blocks
            else:
                headers = [
                    h.format_tex(context=context)
                        if isinstance(h, TeXWriter) else
                    h
                    for h in headers
                ]
                if self.header_spans is not None:
                    alignments = self.header_alignments
                    if alignments is None:
                        alignments = ["c"] * len(headers)

                    _ = []
                    for hl, hs, hc in zip(headers, self.header_spans, alignments):
                        _.append(
                            TeXMulticolumn(hs, hc, hl).format_tex(context)
                                if hs > 1 else
                            hl
                        )
                    headers = _

        wtf = TableFormatter(
            column_formats,
            headers=headers,
            header_spans=self.header_spans,
            **self.format_opts
        ).format(body) + self.array_newline.strip()
        return [
            wtf
        ]

class TeXTable(TeXBlock):
    tag = 'table'
    modifier = 'ht'
    modifier_type = '[]'
    separator = '\n'
    # array_separator = " & "
    # array_newline = " \\\\\n"
    def __init__(self,
                 headers_or_body,
                 body=None,
                 width=1,
                 caption=None,
                 # label=None,
                 resizeable=False,
                 number_format=None,
                 header_spans=None,
                 **etc
                 ):
        if body is None:
            body = headers_or_body
            headers_or_body = None
        body = [
            TeXArray(headers_or_body, body,
                     number_format=number_format,
                     resizeable=resizeable,
                     header_spans=header_spans
                     )
                if not isinstance(body, TeXWriter) else
            body
        ]
        self.width = width
        self.caption = caption
        # self.label = label
        super().__init__(body, **etc)

    def prep_body(self, context=None, body=None):
        if body is None:
            body = self.body

        base = [
            TeXBlock(
                TeXBlock(
                    body,
                    tag='minipage',
                    modifier_type=["[]", "{}"],
                    modifier=['c', f'{self.width} \\textwidth']
                ),
                tag="center"
            )
        ]
        if self.caption is not None:
            base.append(
                TeXFunction(self.caption, function_name="caption")
                    if not isinstance(self.caption, TeXWriter) else
                self.caption
            )
        if self.label is not None:
            base.append(
                TeXFunction(self.label, function_name="label")
                    if not isinstance(self.label, TeXWriter) else
                self.label
            )
        return [
            b.format_tex(context=context)
            for b in base
        ]

class TeXFunction(TeXWriter):
    function_name = None
    def __init__(self, *args, function_name=None):
        if function_name is None:
            function_name = self.function_name
        self.function_name = function_name
        self.args = args
    def format_tex(self, context=None):
        tag = "\\" + self.function_name
        body = ["{" + self.dispatch_format(b, context) + "}" for b in self.args]
        return tag + "".join(body)

class TeXMulticolumn(TeXFunction):
    function_name = 'multicolumn'
    def __init__(self, width, fmt, body):
        super().__init__(width, fmt, body)

class TeXBold(TeXFunction):
    function_name = 'textbf'

class TeXBracketed(TeXWriter):
    brackets = (None, None)
    def __init__(self, body, brackets=None):
        self.body = body
        if brackets is None:
            brackets = self.brackets
        self.brackets = brackets
    def format_tex(self, context=None):
        l, r = self.brackets
        base = self.dispatch_format(self.body, context)
        return l + base + r

class TeXParenthesized(TeXBracketed):
    brackets = ('\\left(', '\\right)')

class TeXEquation(TeXBlock):
    tag = 'equation'
    context = MathContext
    label_header = 'eq'

########################################################################################################################
#
#       TeX Equations
#
#

#region Equations
class TeXNode(Abstract.Expr):
    def to_ast(self):
        raise NotImplementedError("TeXNodes are for formatting only")
class TeXSuperscript(TeXNode):
    __tag__ = "Superscript"
    __slots__ = ['obj', 'index']
    def __init__(self, obj, index):
        self.obj = obj
        self.index = index
class TeXApply(TeXNode):
    __tag__ = "Apply"
    __slots__ = ['function', 'argument']
    def __init__(self, function, argument):
        self.function = function
        self.argument = argument
class TeXSymbol(Abstract.Name):
    def __call__(self, *args):
        return TeXApply(self, args)

class TeXExpr(TeXWriter):

    @classmethod
    def name(cls, s):
        if isinstance(s, str) and len(s) > 1:
            s = "\\" + s
        return cls(Abstract.Name(s))
    @classmethod
    def symbol(cls, s):
        if isinstance(s, str) and len(s) > 1:
            s = "\\" + s
        return cls(TeXSymbol(s))

    # a, b, c, f, g, i, j, k, l, m, n, x, y, z = Abstract.vars(
    #     'a', 'b', 'c', 'f', 'g', 'i', 'j', 'k', 'l', 'm', 'n',
    #     'x', 'y', 'z'
    # )
    # omega, nu, tau, psi, phi, sigma = Abstract.vars(
    #     '\\omega', '\\nu', '\\tau', '\\psi', '\\phi', '\\sigma'
    # )
    # Omega, Nu, Tau, Psi, Phi, Sigma = Abstract.vars(
    #     '\\Omega', '\\Nu', '\\Tau', '\\Psi', '\\Phi', '\\Sigma'
    # )
    # sum, int, prod, bra, ket, braket = Abstract.vars(
    #     '\\sum', '\\int', '\\prod',
    #     '\\bra', '\\ket', '\\braket',
    #     symbol_type=TeXSymbol
    # )

    def __init__(self, body):
        if not isinstance(body, Abstract.Expr):
            body = Abstract.Name(body)
        self.body = body
    def __add__(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body + other)
    def __radd__(self, other):
        return type(self)(other + self.body)
    def __mul__(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body * other)
    def __rmul__(self, other):
        return type(self)(other * self.body)
    def __pow__(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body ** other)
    def __neg__(self):
        return type(self)(-self.body)
    def __xor__(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body ^ other)
    def __or__(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body | other)
    def __getitem__(self, item):
        return type(self)(self.body[item])

    def Equals(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body.Equals(other))
    Eq = Equals
    def LessThan(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body.LessThan(other))
    Lt = LessThan
    def LessEquals(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body.LessEquals(other))
    LtE = LessEquals
    def GreaterThan(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body.GreaterThan(other))
    Gt = GreaterThan
    def GreaterEquals(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body.GreaterEquals(other))
    GtE = GreaterEquals

    @staticmethod
    def convert_name(name, converter):
        name = name.name
        if hasattr(name, 'format_tex'):
            name = name.format_tex()
        return name
    @staticmethod
    def convert_const(const, converter):
        return const.value
    @staticmethod
    def convert_call(call, converter):
        return "{}({})".format(
            converter(call.fn),
            ",".join(converter(k) for k in call.args)
        )
    @staticmethod
    def convert_superscript(op, converter):
        return "{}^{{{}}}".format(
            converter(op.obj),
            converter(op.index)
        )
    @staticmethod
    def convert_bitxor(op, converter):
        return "{}^{{{}}}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_power(op, converter):
        return "{}^{{{}}}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_subscript(op, converter):
        idx = op.index
        if isinstance(idx, slice):
            var = idx.start
            min = idx.stop
            max = idx.step
            if max is None:
                return "{}_{{{}={}}}".format(
                    converter(op.obj),
                    converter(var),
                    converter(min)
                )
            else:
                return "{}_{{{}={}}}^{{{}}}".format(
                    converter(op.obj),
                    converter(var),
                    converter(min),
                    converter(max)
                )
        else:
            return "{}_{{{}}}".format(
                converter(op.obj),
                converter(op.index)
            )
    @staticmethod
    def convert_add(op, converter):
        return "{}+{}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_sub(op, converter):
        return "{}-{}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_mul(op, converter):
        return "{} {}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_bitor(op, converter):
        return "{} {}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_div(op, converter):
        return "\\frac{{{}}{{{}}}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_eq(op, converter):
        return "{} = {}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_raw(obj, converter):
        if hasattr(obj, 'format_tex'):
            return obj.format_tex()
        else:
            return TeXBlock(obj, separator=", ").format_tex()

    @property
    def converter_dispatch(self):
        return {
            'Name':self.convert_name,
            'Const':self.convert_const,
            'Superscript':self.convert_superscript,
            'Subscript':self.convert_subscript,
            'Pow':self.convert_power,
            'BitXOr':self.convert_bitxor,
            'BitOr':self.convert_bitor,
            'Add':self.convert_add,
            'Sub':self.convert_sub,
            'Mul':self.convert_mul,
            'Div':self.convert_div,
            'Equals':self.convert_eq,
            None:self.convert_raw
        }

    def format_tex(self, context=None):
        if context is None:
            context = TeXContextManager.resolve()
        elif isinstance(context, str):
            context = TeXContextManager.resolve(context)

        pad_dollars = not context.math_mode
        with context.subcontext(MathContext):
            expr = self.body.transmogrify(
                self.converter_dispatch
            )
        if pad_dollars:
            expr = '${}$'.format(expr)

        return expr

#endregion

########################################################################################################################
#
#       Wrapper
#
#

class TeX:
    """
    Namespace for TeX-related utilities, someday might help with document prep from templates
    """

    Writer = TeXWriter

    Block = TeXBlock
    Row = TeXRow

    Expr = TeXExpr
    Symbol = TeXExpr.name
    Function = TeXExpr.symbol

    Array = TeXArray
    Table = TeXTable
    Equation = TeXEquation

    wrap_parens = TeXParenthesized

    bold = TeXBold

    @classmethod
    def Matrix(cls, mat, **kwargs):
        return cls.wrap_parens(cls.Array(mat, **kwargs))

class TeXImportGraph:
    import_heads = ("input", "import", "module", "loadsec", "loadfig", "loadtab")
    def __init__(self, tex_root,
                 root_dir=None,
                 head_parser=None,
                 import_heads=None,
                 strip_comments=True,
                 aliases=None,
                 ignored_files=None,
                 **parser_options
                 ):
        if root_dir is None:
            root_dir = os.path.dirname(tex_root)
        self.root = tex_root
        self.root_dir = root_dir
        self.graph = {}
        self._initialized = False
        if import_heads is None:
            import_heads = self.import_heads
        self.import_heads = import_heads
        if head_parser is None:
            head_parser = self.head_resolver
        self.head_parser = head_parser
        self.strip_comments = strip_comments
        self.aliases = aliases
        self.parser_options = parser_options

    @classmethod
    def import_parser(cls, head:str, tag:str):
        return tag.partition(head)[2].strip("{}").strip()+".tex", {}
    @classmethod
    def head_resolver(cls, tag:str):
        return tag.strip()[1:].partition("{")[0].partition("[")[0]
    module_root = "sections"
    @classmethod
    def load_module_parser(cls, tag:str):
        root = tag.partition('module')[2].strip("{}").strip()
        file = os.path.join(cls.module_root, root, "main.tex")
        return file, {'root':os.path.join(cls.module_root, root)}
    @classmethod
    def load_block_parser(cls, head:str, root, tag:str):
        filename = tag.partition(head)[2].strip("{}").strip()
        file = os.path.join(root, filename + ".tex")
        ref = head[4:]
        if ref not in {'fig', 'tab', 'eq'}:
            opts = {'header': f'\\label{{{ref}:{filename}}}\n'}
        else:
            opts = {}
        return file, opts
    @classmethod
    def resolve_parser(cls, head:str):
        if head == 'module':
            return cls.load_module_parser
        elif head.startswith("load"):
            subhead = head[4:]
            if subhead == 'sec':
                root = 'sections'
            elif subhead == 'fig':
                root = 'figures'
            elif subhead == 'tab':
                root = 'tables'
            else:
                root = subhead
            return functools.partial(cls.load_block_parser, head, root)
        else:
            return functools.partial(cls.import_parser, head)

    ImportNode = collections.namedtuple("ImportNode", ["root_dir", "end_points", "head", "block", "opts"])
    root_dir_var = r"\RootDirectory"
    def _resolve_aliases(self, root_dir):
        base_aliases = {
            self.root_dir_var:root_dir
        }
        if self.aliases is not None:
            for a,v in self.aliases.items()  :
                if not isinstance(v, str):
                    v = v(base_aliases)
                else:
                    for rep_from,rep_to in base_aliases.items():
                        v = v.replace(rep_from, rep_to)
                base_aliases[a] = v
        return base_aliases
    def _handle_parse_block(self, parser, head_map, import_heads, root_dir):
        imports = {}
        ep, block = parser.parse_tex_call(import_heads, return_end_points=True)
        aliases = self._resolve_aliases(root_dir)
        while block is not None:
            head = self.head_parser(block)
            filename, opts = head_map[head](block)
            for rep_from,rep_to in aliases.items():
                filename = filename.replace(rep_from, rep_to)
            if not filename.startswith("/"):
                file = os.path.join(root_dir, filename)
            else:
                file = filename
            imports[file] = self.ImportNode(root_dir, ep, head, block, opts)
            ep, block = parser.parse_tex_call(import_heads, return_end_points=True)
        return imports
    @classmethod
    def strip_tex_comments(cls, body):
        body = re.sub(r"($|^)%.*\n", "", body)
        body = re.sub(r"(?<!\\)%.*\n", "", body)
        return body
    def find_imports(self, root=None, import_heads=None, root_dir=None) -> dict[str, ImportNode]:
        if root is None:
            root = self.root
        if import_heads is None:
            import_heads = self.import_heads
        if root_dir is None:
            root_dir = self.root_dir

        if isinstance(import_heads, dict):
            head_map = import_heads
        else:
            head_map = {
                k:self.resolve_parser(k)
                for k in import_heads
            }
        if self.strip_comments:
            with tf.TemporaryFile(mode='w+') as new_root:
                new_body = self.strip_tex_comments(dev.read_file(root))
                new_root.write(new_body)
                new_root.seek(0)
                with Parsers.TeXParser(new_root, **self.parser_options) as parser:
                    imports = self._handle_parse_block(parser, head_map, import_heads, root_dir)
        else:
            with Parsers.TeXParser(root, **self.parser_options) as parser:
                imports = self._handle_parse_block(parser, head_map, import_heads, root_dir)
        return imports

    verbose = False
    def populate_graph(self, import_heads=None, root_dir=None):
        if root_dir is None:
            root_dir = self.root_dir
        if not self._initialized:
            self._initialized = True
            queue = collections.deque([(self.root, root_dir)])
            while queue:
                root, root_dir = queue.pop()
                new_imports = self.find_imports(root, import_heads=import_heads, root_dir=root_dir)
                new_imports = {
                    file: node
                    for file, node in new_imports.items()
                    if file not in self.graph
                }
                clean_imports = {}
                for file,node in new_imports.items():
                    if not os.path.isfile(file):
                        if self.verbose:
                            print(f"IGNORING MISSING FILE: {file}")
                    else:
                        clean_imports[file] = node
                new_imports = clean_imports
                self.graph[root] = new_imports
                for file, node in new_imports.items():
                    subroot = node.opts.get('root')
                    if subroot is not None:
                        subdir = os.path.join(root_dir, subroot)
                    else:
                        subdir = root_dir
                    queue.append((file, subdir))

        return self.graph

class TeXTranspiler:
    def __init__(self,
                 tex_root,
                 root_dir=None,
                 figure_renaming_function=None,
                 bib_renaming_function=None,
                 strip_comments=True,
                 figures_path=None,
                 figure_merge_function=None,
                 bib_path=None,
                 bib_merge_function=None,
                 bib_cleanup_function=None,
                 citation_renaming_function=None,
                 aliases=None,
                 styles_path=None,
                 parser_options=None
                 ):
        if parser_options is None:
            parser_options = {}
        self.graph = TeXImportGraph(tex_root,
                                    root_dir=root_dir,
                                    strip_comments=strip_comments,
                                    aliases=aliases,
                                    **parser_options
                                    )
        self.figure_renaming_function = figure_renaming_function
        self.figures_path = figures_path
        self.figure_merge_function = figure_merge_function
        self.bib_renaming_function = bib_renaming_function
        self.bib_path = bib_path
        self.bib_merge_function = bib_merge_function
        self.bib_cleanup_function = bib_cleanup_function
        self.citation_renaming_function = citation_renaming_function
        self.styles_path = styles_path
        self.parser_options = parser_options

    @classmethod
    def figure_counter(cls, name_root="Figure", start_at=1):
        counter = itertools.count()
        for _ in range(start_at):
            next(counter)
        return lambda fig: f"{name_root}{next(counter)}" + os.path.splitext(fig)[1]

    @classmethod
    def add_bibs(cls, bib_list):
        bib_bodies = []
        for b in bib_list:
            if not os.path.isfile(b) and os.path.splitext(b)[-1] == "":
                b = b + ".bib"
            bib_bodies.append(dev.read_file(b))
        body = "\n\n".join(bib_bodies)
        with tf.NamedTemporaryFile('w+', delete=False) as temp:
            temp.write(body)
        return temp.name, True

    @classmethod
    def pruned_bib(cls, bib_file_or_filter,  cites=None, *, filter=None, **parser_options):
        if filter is None and cites is None:
            def prune_bib(bib_file, cites):
                return cls.pruned_bib(bib_file, cites=cites, filter=bib_file_or_filter, **parser_options)
            return prune_bib
        else:
            bib_file = bib_file_or_filter

            if filter is not None:
                cites = filter(cites)

            allowed_cites = {
                r
                for label in cites.values()
                for r in label.ref
            }

            blocks = []
            with Parsers.BibTeXParser(bib_file, **parser_options) as parser:
                (s, e), text = parser.parse_bib_item(return_end_points=True)
                while text is not None:
                    keys = parser.parse_bib_body(text, parse_lines=False)
                    if keys['key'] in allowed_cites:
                        blocks.append(text)
                    (s, e), text = parser.parse_bib_item(return_end_points=True)


            dev.write_file(bib_file, "\n\n".join(blocks))

    @classmethod
    def get_injection_body(cls, root_dir, node_data:TeXImportGraph.ImportNode, body:str):
        # here to be overridden
        if root_dir is not None:
            root = dev.drop_directory_prefix(root_dir, node_data.root_dir)
        else:
            root = node_data.root_dir
        if len(root) > 0 and not root.endswith("/"):
            root = root + "/"
        body = (
            node_data.opts.get('header', "")
            + body.replace("\\RootDirectory/", root)
            + node_data.opts.get('footer', "")
        )
        return node_data.end_points, body

    @classmethod
    def apply_body_edit(cls, cur_text, edits, normalization_function=None):
        chunks = []
        split_point = 0
        if hasattr(edits, 'items'):
            edits = edits.items()
        clean_edits = [
            normalization_function(node_data, body)
                if normalization_function is not None else
            (node_data, body)
            for node_data, body in edits
        ]
        for (s,e), body in sorted(clean_edits, key=lambda se: se[0][0]):
            s = s - split_point
            start_chunk = cur_text[:s]
            chunks.append(start_chunk)
            chunks.append(body)
            if e > 0:
                e = e - split_point
                cur_text = cur_text[e:]
                split_point = split_point + e
            else:
                cur_text = ""
        chunks.append(cur_text)

        return "".join(chunks)

    @classmethod
    def flatten_import_graph(cls,
                             graph:dict[str, dict[str, TeXImportGraph.ImportNode]],
                             root,
                             cache=None,
                             root_dir=None,
                             strip_comments=False
                             ):
        if cache is None:
            cache = {}
        if root in cache:
            return cache[root]

        cache[root] = None # to break cycles

        edits = []
        for file,node_data in graph[root].items():
            if file not in cache:
                cache[file] = cls.flatten_import_graph(graph, file, cache=cache, root_dir=root_dir, strip_comments=strip_comments)
            edits.append([node_data, cache[file]])

        cur_text = dev.read_file(root)
        if strip_comments:
            cur_text = TeXImportGraph.strip_tex_comments(cur_text)
        edit_block = cls.apply_body_edit(
            cur_text, edits,
            normalization_function=lambda node_data, body:cls.get_injection_body(root_dir, node_data, body)
        )

        cache[root] = edit_block

        return cache[root]

    def remap_block(self, flat_tex, call_head, file_parser, replacement_path=None, renaming_function=None):
        blocks = None
        if os.path.isfile(flat_tex):
            temp_tex = flat_tex
            flat_tex = dev.read_file(flat_tex)
            if self.graph.strip_comments:
                flat_tex = TeXImportGraph.strip_tex_comments(flat_tex)
            else:
                with Parsers.TeXParser(temp_tex) as parser:
                    ep, block = parser.parse_tex_call(call_head, return_end_points=True)
                    while block is not None:
                        blocks[ep] = block
                        ep, block = parser.parse_tex_call(call_head, return_end_points=True)

        if blocks is None:
            with tf.TemporaryFile(mode="w+") as temp_tex:
                temp_tex.write(flat_tex)
                temp_tex.seek(0)
                with Parsers.TeXParser(temp_tex) as parser:
                    blocks = {}
                    ep, block = parser.parse_tex_call(call_head, return_end_points=True)
                    while block is not None:
                        blocks[ep] = block
                        ep, block = parser.parse_tex_call(call_head, return_end_points=True)

        filenames = [ file_parser(v) for v in blocks.values() ]

        if replacement_path is not None:
            repathing = functools.partial(self._repath_resource, replacement_path)
            if renaming_function is None:
                renaming_function = repathing
            else:
                renaming_function = lambda figure, _renaming=renaming_function : repathing(figure, _renaming)

        if renaming_function is not None:
            filenames = {
                k: renaming_function(k)
                for k in filenames
            }
            flat_tex = self.apply_body_edit(
                flat_tex, blocks,
                normalization_function=lambda edit_pos, body: (
                    edit_pos,
                    self._modify_resource_path(body, filenames)
                )
            )

        return flat_tex, filenames

    @classmethod
    def _repath_resource(cls, new_root, figure_path, renaming_function=None):
        if isinstance(figure_path, str):
            if renaming_function is not None:
                basename = renaming_function(figure_path)
            else:
                basename = os.path.basename(figure_path)
            return os.path.join(new_root, basename)
        else:
            if renaming_function is not None:
                figure_path = renaming_function(figure_path)
                if isinstance(figure_path, str):
                    return os.path.join(new_root, figure_path)
            return ",".join(cls._repath_resource(new_root, fp) for fp in figure_path)
    @classmethod
    def _parse_graphics_file(cls, tag:str):
        files = tuple(s.strip() for s in tag.partition("{")[-1].partition("}")[0].split(","))
        if len(files) == 1:
            files = files[0]
        return files
    @classmethod
    def _modify_resource_path(cls, tag:str, file_map):
        head, _, path = tag.partition("{")
        name, _, rest = path.partition("}")
        names = tuple(s.strip() for s in name.split(","))
        if len(names) == 1:
            names = names[0]
        return head + "{" + file_map[names] + "}" + rest
    def remap_figures(self, flat_tex, figures_path=None):
        if figures_path is None:
            figures_path = self.figures_path
        return self.remap_block(flat_tex, "includegraphics", self._parse_graphics_file,
                                replacement_path=figures_path,
                                renaming_function=self.figure_renaming_function)

    def remap_bibliography(self, flat_tex, bib_path=None):
        if bib_path is None:
            bib_path = self.bib_path
        return self.remap_block(flat_tex, "bibliography",
                                self._parse_graphics_file,
                                replacement_path=bib_path,
                                renaming_function=self.bib_renaming_function)

    def remap_style_files(self, flat_tex, styles_path=None):
        if styles_path is None:
            styles_path = self.styles_path
        flat_tex, classes = self.remap_block(flat_tex,
                                "documentclass",
                                self._parse_graphics_file,
                                replacement_path=styles_path)
        classes = [os.path.splitext(c)[0]+".cls" for c in classes]

        flat_tex, bib_styles = self.remap_block(flat_tex,
                                "bibliographystyle",
                                self._parse_graphics_file,
                                replacement_path=styles_path)
        bib_styles = [os.path.splitext(c)[0]+".bst" for c in bib_styles]
        return flat_tex, (classes + bib_styles)


    @classmethod
    def get_call_list(self, tex_stream, tags) -> dict[tuple[int, int], str]:
        blocks = {}
        with dev.StreamInterface(tex_stream, file_backed=True) as stream:
            with Parsers.TeXParser(stream) as parser:
                ep, block = parser.parse_tex_call(tags, return_end_points=True)
                while block is not None:
                    blocks[ep] = block
                    ep, block = parser.parse_tex_call(tags, return_end_points=True)

        return blocks
    @classmethod
    def _parse_label_ref(cls, l:str):
        head, _, tag = l.partition('{')
        tag_type, _, tag_ref = tag.partition('}')[0].partition(":")
        head = head.strip("\\").partition("[")[0]
        return head, tag_type.strip(), tag_ref.strip()
    LabelBlock = collections.namedtuple("LabelBlock", ["tag", "ref", "end_points", "head", "block"])
    @classmethod
    def create_label_block_map(cls, tex_stream, call_tags, block_parser):
        maps = {}
        for ep, l in cls.get_call_list(tex_stream, call_tags).items():
            head, tag_type, tag_ref = block_parser(l)
            if len(tag_ref) == 0:
                tag_type, tag_ref = None, tag_type
            if tag_type not in maps:
                maps[tag_type] = {}
            maps[tag_type][ep] = cls.LabelBlock(tag_type, tag_ref, ep, head, l)
        return maps
    @classmethod
    def create_label_map(cls, tex_stream):
        return cls.create_label_block_map(tex_stream, 'label', cls._parse_label_ref)

    @classmethod
    def _parse_ref_ref(cls, l):
        refs = l.split('{')
        head, refs = refs[0], refs[1:]
        head = head.strip("\\").partition("[")[0]
        refs = [r.partition("}")[0] for r in refs]
        if ":" in refs[0]:
            tag_type, _, tag_ref = [r.strip() for r in refs[0].partition(":")]
        else:
            tag_type = head[3:]
            if head.endswith("s"):
                tag_type = tag_type[:-1]
                tag_ref = {'refs':refs, 'type':'pair'}
            elif head.endswith('rng'):
                tag_type = tag_type[:-3]
                tag_ref = {'refs':refs, 'type':'range'}
            else:
                tag_ref = refs[0]
        return head, tag_type, tag_ref
    @classmethod
    def create_ref_map(cls, tex_stream):
        return cls.create_label_block_map(tex_stream,
                                          ('ref',
                                           'reffig', 'reftab', 'refeq', 'refsec',
                                           'reffigs', 'reftabs', 'refeqs', 'refsecs',
                                           'reffigrng', 'reftabrng', 'refeqrng', 'refsecrng',
                                           ),
                                          cls._parse_ref_ref)

    @classmethod
    def _parse_cite_ref(cls, l):
        head, _, body = l.partition('{')
        head = head.strip("\\").partition("[")[0]
        cites = [s.strip() for s in body.partition("}")[0].split(",")]
        return head, "cite", cites
    @classmethod
    def create_cite_map(cls, tex_stream):
        return cls.create_label_block_map(tex_stream,
                                          'cite',
                                          cls._parse_cite_ref)
    @classmethod
    def remap_citation_set(cls, tex_stream, ref_handler, cite_map=None):
        if cite_map is None:
            cite_map = cls.create_cite_map(tex_stream)
        edits = ref_handler(cite_map)
        return cls.apply_body_edit(tex_stream, edits)

    @classmethod
    def _rename_cites(cls, citations, renaming):
        return {
            eps:f"\\{label.head}" + "{" + ",".join(renaming(l) for l in label.refs) + "}"
            for eps,label in citations.items()
        }
    def remap_citations(self, flat_tex, si_tex:dict[str,str]=None, citation_renaming_function=None):
        citations = self.create_cite_map(flat_tex)
        if si_tex is not None:
            for name,tex in si_tex.items():
                citations = dev.merge_dicts(citations, self.create_cite_map(tex))
        if len(citations) > 0:
            citations = citations['cite']
            if citation_renaming_function is not None:
                citation_renaming_function = self.citation_renaming_function
            if citation_renaming_function is not None:
                flat_tex = self.remap_citation_set(flat_tex,
                                                   lambda cites:self._rename_cites(cites, citation_renaming_function),
                                                   citations)
        return flat_tex, citations

    ref_tag_map = {
        'sec': ("Sec.", "Secs."),
        'fig': ("Fig.", "Figs."),
        'tab': ("Table", "Tables"),
        'eq': ("Eq.", "Eqs.")
    }
    ref_label_formats = {
        'single': "{tag} {index}",
        'pair': "{tag} {index[0]} and {index[1]}",
        'range': "{tag} {index[0]}-{index[1]}",
    }
    si_ref_format = "S{i}"
    main_ref_format = "ref{{{ref}}}"
    @classmethod
    def ref_remapping_label(cls, head, label, si_index_map):
        if isinstance(label.ref, str):
            if (head, label.ref) in si_index_map:
                return cls.ref_label_formats['single'].format(
                    tag=cls.ref_tag_map[head][0],
                    index=cls.si_ref_format.format(i=si_index_map[(head, label.ref)] + 1)
                )
            else:
                return None
        else:
            if any((head, r) in si_index_map for r in label.ref['refs']):
                fmt = cls.ref_label_formats[label.ref['type']]
                tag = cls.ref_tag_map[head][1]
                index = [
                    cls.si_ref_format.format(i=si_index_map[(head, r)] + 1)
                        if (head, r) in si_index_map else
                    cls.main_ref_format.format(r)
                    for r in label.ref['refs']
                ]
                return fmt.format(tag=tag, index=index)
            else:
                return None

    @classmethod
    def figure_table_remapping(cls, si_labels:dict[str, dict[tuple[int, int], LabelBlock]], label_function=None):
        si_ref_map = {}
        for head, labels in si_labels.items():
            for index,(_, label) in enumerate(labels.items()):
                si_ref_map[(head, label.ref)] = index

        if label_function is None:
            label_function = cls.ref_remapping_label

        def handle_refs(ref_map:dict[str, dict[tuple[int, int], cls.LabelBlock]]):
            edits = {}
            for head, labels in ref_map.items():
                for eps, label in labels.items():
                    label = label_function(head, label, si_ref_map)
                    if label is not None:
                        edits[eps] = label
            return edits
        return handle_refs
    @classmethod
    def remap_refs(cls, tex_stream, ref_handler, ref_map=None):
        if ref_map is None:
            ref_map = cls.create_ref_map(tex_stream)
        edits = ref_handler(ref_map)
        return cls.apply_body_edit(tex_stream, edits)

    si_doc_labels = ('referenceExternalDocument',)
    @classmethod
    def find_si_documents(cls, flat_tex):
        si_docs = {}
        for ep, l in cls.get_call_list(flat_tex, cls.si_doc_labels).items():
            doc_name = l.partition("{")[-1].partition("}")[0].strip()
            si_docs[doc_name] = ep
        return si_docs

    def remap_si(self, flat_tex):
        docs = self.find_si_documents(flat_tex)
        flat_docs = {
            t:type(self)(
                os.path.join(self.graph.root_dir, os.path.splitext(t)[0] + ".tex"),
                root_dir=self.graph.root_dir
            ).create_flat_tex(include_aux=False)
            for t in docs.keys()
        }

        #TODO: infer label style
        si_labels = {}
        for doc in flat_docs.values():
            si_labels = dev.merge_dicts(si_labels, self.create_label_map(doc))

        if len(si_labels) > 0:
            flat_tex = self.apply_body_edit(flat_tex, {e:"" for e in docs.values()})
            flat_tex = self.remap_refs(flat_tex, self.figure_table_remapping(si_labels))

        return flat_tex, flat_docs

    def create_flat_tex(self, include_aux=True):
        flat_tex = self.flatten_import_graph(
            self.graph.populate_graph(),
            self.graph.root,
            root_dir=self.graph.root_dir,
            strip_comments=self.graph.strip_comments
        )

        if include_aux:
            flat_tex, style_files = self.remap_style_files(flat_tex)
            flat_tex, figure_files = self.remap_figures(flat_tex)
            flat_tex, bib_files = self.remap_bibliography(flat_tex)
            flat_tex, si_tex = self.remap_si(flat_tex)
            flat_tex, cites = self.remap_citations(flat_tex, si_tex)
            # flat_tex = self.remap_si

            aux = {
                'styles':style_files,
                'figures':figure_files,
                'bibliography':bib_files,
                'si':si_tex,
                'citations': cites
            }

            return flat_tex, aux
        else:
            return flat_tex

    @classmethod
    def _copy_inputs(cls, root_dir, target_dir, resource_path, inputs, merge_function,
                     search_paths=None,
                     allow_missing=False,
                     post_processor=None
                     ):
        if resource_path is not None:
            fig_dir = os.path.join(target_dir, resource_path)
            os.makedirs(fig_dir, exist_ok=True)
        else:
            fig_dir = target_dir

        if not hasattr(inputs, 'items'):
            inputs = {k:os.path.basename(k) for k in inputs}
        for src, target in inputs.items():
            requires_delete = False
            if not isinstance(target, str):
                if isinstance(src, str):
                    raise ValueError(f"can't map single source file ({src}) to multiple outputs ({target})")
                elif len(src) != len(target):
                    raise ValueError(f"can't map {len(src)} source files to {len(target)} outputs ({src} to {target})")
            elif not isinstance(src, str):
                src, requires_delete = merge_function([os.path.join(root_dir, s) for s in src])
                if not isinstance(src, str):
                    if requires_delete:
                        os.remove(src)
                    raise ValueError(f"can't map non string source ({src}) to {target}")
            else:
                src = os.path.join(root_dir, src)

            if isinstance(src, str):
                src = [src]
                target = [target]
            try:
                for s, d in zip(src, target):
                    if not os.path.isfile(s):
                        if search_paths is not None:
                            s_dir, s_base = os.path.split(s)
                            for p in search_paths:
                                test = os.path.join(s_dir, p, s_base)
                                if os.path.isfile(test):
                                    s = test
                                    break
                    if allow_missing and not os.path.isfile(s):
                        continue
                    targ = os.path.join(fig_dir, d)
                    shutil.copy(s, targ)
                    if post_processor is not None:
                        post_processor(targ)
            finally:
                if requires_delete:
                    for s in src: os.remove(s)


    style_search_paths = ["styles"]
    def transpile(self, target_dir, file_name='main.tex', include_si=True, include_aux=True, allow_missing_styles=False):
        flat_file = self.create_flat_tex(include_aux=include_aux)
        os.makedirs(target_dir, exist_ok=True)
        if include_aux:
            flat_file, aux = flat_file
            if 'styles' in aux:
                self._copy_inputs(self.graph.root_dir, target_dir,
                                  self.styles_path,
                                  aux['styles'],
                                  self.figure_merge_function,
                                  search_paths=self.style_search_paths,
                                  allow_missing=allow_missing_styles
                                  )
            if 'figures' in aux:
                self._copy_inputs(self.graph.root_dir, target_dir, self.figures_path, aux['figures'], self.figure_merge_function)

            if 'citations' in aux:
                if self.bib_cleanup_function is not None:
                    bib_post_processor = lambda file:self.bib_cleanup_function(file, aux['citations'], **self.parser_options)
                else:
                    bib_post_processor = None
                self._copy_inputs(self.graph.root_dir, target_dir, self.bib_path, aux['bibliography'],
                                  self.bib_merge_function,
                                  post_processor=bib_post_processor
                                  )
            if include_si and 'si' in aux:
                for name,flat in aux['si'].items():
                    dev.write_file(os.path.join(target_dir, name+'.tex'), flat)

        os.path.join(target_dir, file_name)
        dev.write_file(os.path.join(target_dir, file_name), flat_file)
        return target_dir

    # @classmethod
    # def condense_bibtex(cls, source_tex):
    #     ...
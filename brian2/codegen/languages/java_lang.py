'''
TODO: use preferences to get arguments to Language
'''
import itertools
import os

import numpy

from brian2.utils.stringtools import deindent, stripped_deindented_lines
from brian2.codegen.functions.base import Function
from brian2.utils.logger import get_logger

from .base import Language
from brian2.parsing.rendering import CPPNodeRenderer

from brian2.core.preferences import brian_prefs, BrianPreference

logger = get_logger(__name__)

__all__ = ['JavaLanguage',
           'java_data_type',
           ]


def java_data_type(dtype):
    '''
    Gives the Java language specifier for numpy data types. For example,
    ``numpy.int32`` maps to ``int`` in Java.

    Java has no unsigned types, so if an unsigned datatypes is requested
    the next largest type is used instead.
    '''
    if dtype == numpy.int:
        dtype = 'int'
    if dtype == numpy.float32:
        dtype = 'float'
    elif dtype == numpy.float64:
        dtype = 'double'
    elif dtype == numpy.int32:
        dtype = 'int'
    elif dtype == numpy.int64:
        dtype = 'long'
    elif dtype == numpy.uint16:
        dtype = 'short'
    elif dtype == numpy.uint32:
        dtype = 'long'
    elif dtype == numpy.bool_ or dtype is bool:
        dtype = 'boolean'
    else:
        raise ValueError("dtype " + str(dtype) + " not known.")
    return dtype


# Preferences
brian_prefs.register_preferences(
    'codegen.languages.java',
    'Java codegen preferences',
    )


class JavaLanguage(Language):
    '''
    Java language

    Java code templates should provide Jinja2 macros with the following names:

    ``main``
        The main loop.
    ``support_code``
        The support code (function definitions, etc.), compiled in a separate
        file.

    For user-defined functions, there are two keys to provide:

    ``support_code``
        The function definition which will be added to the support code.

    See `TimedArray` for an example of these keys.
    '''

    language_id = 'java'

    def __init__(self):
        # set default prefs???
        pass

    def translate_expression(self, expr):
        return CPPNodeRenderer().render_expr(expr).strip()

    def translate_statement(self, statement):
        var, op, expr = statement.var, statement.op, statement.expr
        if op == ':=':
            decl = java_data_type(statement.dtype) + ' '
            op = '='
            if statement.constant:
                decl = 'const ' + decl
        else:
            decl = ''
        return decl + var + ' ' + op + ' ' +\
                self.translate_expression(expr) + ';'

    def translate_statement_sequence(self, statements, specifiers,
                                                     namespace, indices):
        read, write = self.array_read_write(statements, specifiers)
        lines = []
        # read arrays
        for var in read:
            index_var = specifiers[var].index
            index_spec = indices[index_var]
            spec = specifiers[var]
            if var not in write:
                line = 'const '
            else:
                line = ''
            line = line + java_data_type(spec.dtype) + ' ' + var + ' = '
            line = line + spec.arrayname + '[' + index_var + '];'
            lines.append(line)
        # simply declare variables that will be written but not read
        for var in write:
            if var not in read:
                spec = specifiers[var]
                line = java_data_type(spec.dtype) + ' ' + var + ';'
                lines.append(line)
        # the actual code
        lines.extend([self.translate_statement(stmt) for stmt in statements])
        # write arrays
        for var in write:
            index_var = specifiers[var].index
            index_spec = indices[index_var]
            spec = specifiers[var]
            line = spec.arrayname + '[' + index_var + '] = ' + var + ';'
            lines.append(line)
        code = '\n'.join(lines)
        lines = []
        # set up the functions
        user_functions = []
        support_code = ''
        for var, spec in itertools.chain(namespace.items(),
                                         specifiers.items()):
            if isinstance(spec, Function):
                user_functions.append(var)
                speccode = spec.code(self, var)
                support_code += '\n' + deindent(speccode['support_code'])
        # delete the user-defined functions from the namespace
        for func in user_functions:
            del namespace[func]

        # return
        return (stripped_deindented_lines(code),
                {
                    'support_code_lines': stripped_deindented_lines(support_code),
                    # 'denormals_code_lines': stripped_deindented_lines(self.denormals_to_zero_code()),
                 })


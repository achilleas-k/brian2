'''
TODO: use preferences to get arguments to Language
'''

import numpy

from brian2.utils.stringtools import deindent, stripped_deindented_lines
from brian2.codegen.functions.base import Function
from brian2.utils.logger import get_logger
from brian2.parsing.rendering import JavaNodeRenderer
from brian2.core.preferences import brian_prefs, BrianPreference
from brian2.core.variables import ArrayVariable

from .base import Language

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

    Each
    '''
    if dtype == numpy.int:
        dtype = {'java': 'int', 'renderscript': 'int32_t', 'allocation': 'I32'}
    elif dtype == numpy.float32:
        dtype = {'java': 'float', 'renderscript': 'float', 'allocation': 'F32'}
    elif dtype == numpy.float64:
        # NOTE: Using float instead of double
        dtype = {'java': 'float', 'renderscript': 'float', 'allocation': 'F32'}
        #dtype = {'java': 'double', 'renderscript':'double', 'allocation': 'F64'}
    elif dtype == numpy.int32:
        dtype = {'java': 'int', 'renderscript': 'int32_t', 'allocation': 'I32'}
    elif dtype == numpy.int64:
        dtype = {'java': 'long', 'renderscript': 'int64_t', 'allocation': 'I64'}
    elif dtype == numpy.uint16:
        dtype = {'java': 'short', 'renderscript': 'int16_t', 'allocation': 'I16'}
    elif dtype == numpy.uint32:
        dtype = {'java': 'long', 'renderscript': 'int64_t', 'allocation': 'I64'}
    elif dtype == numpy.bool_ or dtype is bool:
        dtype = {'java': 'boolean', 'renderscript': 'bool', 'allocation': 'BOOLEAN'}
    else:
        raise ValueError("dtype " + str(dtype) + " not known.")
    return dtype


# Preferences
brian_prefs.register_preferences(
    'codegen.languages.java',
    'Java codegen preferences',
    restrict_keyword = BrianPreference(
        default='__restrict__',
        docs='''
        The keyword used for the given compiler to declare pointers as restricted.

        This keyword is different on different compilers, the default is for gcc.
        ''',
        ),
    flush_denormals = BrianPreference(
        default=False,
        docs='''
        Adds code to flush denormals to zero.

        The code is gcc and architecture specific, so may not compile on all
        platforms. The code, for reference is::

            #define CSR_FLUSH_TO_ZERO         (1 << 15)
            unsigned csr = __builtin_ia32_stmxcsr();
            csr |= CSR_FLUSH_TO_ZERO;
            __builtin_ia32_ldmxcsr(csr);

        Found at `<http://stackoverflow.com/questions/2487653/avoiding-denormal-values-in-c>`_.
        ''',
        ),
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

    def __init__(self, java_data_type=java_data_type):
        self.restrict = brian_prefs['codegen.languages.java.restrict_keyword']
        self.flush_denormals = brian_prefs['codegen.languages.java.flush_denormals']
        self.java_data_type = java_data_type

    def translate_expression(self, expr):
        return JavaNodeRenderer().render_expr(expr).strip()

    def translate_statement(self, statement):
        var, op, expr = statement.var, statement.op, statement.expr
        if op == ':=':
            decl = self.java_data_type(statement.dtype)['java'] + ' '
            op = '='
            if statement.constant:
                decl = 'const ' + decl
        else:
            decl = ''
        return decl + var + ' ' + op + ' ' +\
                self.translate_expression(expr) + ';'

    def translate_statement_sequence(self, statements, variables, namespace,
                                     variable_indices, iterate_all):
        # TODO: Clean up! There must be a lot of lines in here that aren't used for the Android object (pointer lines? hash defines?)
        read, write = self.array_read_write(statements, variables)
        lines = []
        # read arrays
        for varname in read:
            index_var = variable_indices[varname]
            var = variables[varname]
            if varname not in write:
                line = 'const '
            else:
                line = ''
            line = line + self.java_data_type(var.dtype)['renderscript'] + ' ' + varname + ' = '
            line = line + '_ptr' + var.arrayname + '[' + index_var + '];' # keep ptr prefix for now
            lines.append(line)
        # simply declare variables that will be written but not read
        for varname in write:
            if varname not in read:
                var = variables[varname]
                line = self.java_data_type(var.dtype)['renderscript'] + ' ' + varname + ';'
                lines.append(line)
        # the actual code
        lines.extend([self.translate_statement(stmt) for stmt in statements])
        # write arrays
        for varname in write:
            index_var = variable_indices[varname]
            var = variables[varname]
            line = '_ptr' + var.arrayname + '[' + index_var + '] = ' + varname + ';'
            lines.append(line)
        code = '\n'.join(lines)
        lines = []
        # It is possible that several different variable names refer to the
        # same array. E.g. in gapjunction code, v_pre and v_post refer to the
        # same array if a group is connected to itself
        arraynames = set()
        for varname, var in variables.iteritems():
            if isinstance(var, ArrayVariable):
                arrayname = var.arrayname
                if not arrayname in arraynames:
                    line = self.java_data_type(var.dtype)['renderscript'] + ' * ' + self.restrict + '_ptr' + arrayname + ' = ' + arrayname + ';'
                    lines.append(line)
                    arraynames.add(arrayname)
        pointers = '\n'.join(lines)
        print "\n----\nThe list of arrays defined in java_lang for : "
        for an in arraynames:
            print an
        print "\nAccompanying code:"
        print code

        print "\nPointers:"
        print pointers
        # set up the functions
        user_functions = []
        support_code = ''
        hash_defines = ''
        #for varname, variable in namespace.items():
        #    if isinstance(variable, Function):
        #        user_functions.append(varname)
        #        speccode = variable.code(self, varname)
        #        support_code += '\n' + deindent(speccode['support_code'])
        #        hash_defines += deindent(speccode['hashdefine_code'])
        #        # add the Python function with a leading '_python', if it
        #        # exists. This allows the function to make use of the Python
        #        # function via weave if necessary (e.g. in the case of randn)
        #        if not variable.pyfunc is None:
        #            pyfunc_name = '_python_' + varname
        #            if pyfunc_name in namespace:
        #                logger.warn(('Namespace already contains function %s, '
        #                             'not replacing it') % pyfunc_name)
        #            else:
        #                namespace[pyfunc_name] = variable.pyfunc

        # delete the user-defined functions from the namespace
        for func in user_functions:
            del namespace[func]

        # return
        return (stripped_deindented_lines(code),
                {'pointers_lines': stripped_deindented_lines(pointers),
                 'support_code_lines': stripped_deindented_lines(support_code),
                 'hashdefine_lines': stripped_deindented_lines(hash_defines),
                 'denormals_code_lines': stripped_deindented_lines(self.denormals_to_zero_code()),
                 })

    def denormals_to_zero_code(self):
        if self.flush_denormals:
            return '''
            #define CSR_FLUSH_TO_ZERO         (1 << 15)
            unsigned csr = __builtin_ia32_stmxcsr();
            csr |= CSR_FLUSH_TO_ZERO;
            __builtin_ia32_ldmxcsr(csr);
            '''
        else:
            return ''

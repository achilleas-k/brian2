import os

from ...codeobject import CodeObject
from ...templates import Templater
from ...languages import java_lang
from ..targets import runtime_targets

from brian2.core.preferences import brian_prefs, BrianPreference
from brian2.core.variables import ArrayVariable, Variable, Subexpression


__all__ = ['JavaCodeObject']

# Preferences
brian_prefs.register_preferences(
    'codegen.runtime.java',
    'Java runtime codegen preferences',
    compiler = BrianPreference(
        default='javac',
        validator=lambda pref: pref=='javac',
        docs='''
        Compiler to use for java.
        ''',
        ),
    extra_compile_args = BrianPreference(
        default=[],
        docs='''
        Extra compile arguments to pass to compiler
        ''',
        ),
    )


class JavaCodeObject(CodeObject):
    '''
    Java code object

    The ``code`` should be a `~brian2.codegen.languages.templates.MultiTemplate`
    object with two macros defined, ``main`` (for the main loop code) and
    ``support_code`` for any support code (e.g. function definitions).
    '''
    templater = Templater(os.path.join(os.path.split(__file__)[0],
                                       'templates'))
    language = java_lang.JavaLanguage()

    def __init__(self, code, namespace, variables, name='codeobject*'):
        super(JavaCodeObject, self).__init__(code, namespace, variables, name=name)

    def variables_to_namespace(self):
        # Variables can refer to values that are either constant (e.g. dt)
        # or change every timestep (e.g. t). We add the values of the
        # constant variables here and add the names of non-constant variables
        # to a list

        # A list containing tuples of name and a function giving the value
        self.nonconstant_values = []
        constants = []
        arrays = []
        functions = []
        for k, v in self.namespace.items():
            if isinstance(v, float):
                # TODO: Use the language submodule to translate
                dtype = "float"
                constants.append((dtype, k, repr(v)+'f'))
            elif isinstance(v, int):
                dtype = "int"
                constants.append((dtype, k, repr(v)))
            elif hasattr(v, '__call__'):
                functions.append((k, v))
        for k, v in self.variables.items():
            if isinstance (v, ArrayVariable):
                dtype_spec = java_lang.java_data_type(v.dtype)
                # TODO: Perhaps it would be more convenient as a dictionary?
                arrays.append((v.arrayname, dtype_spec, len(v.value)))
        self.arrays = arrays
        self.constants = constants
        self.functions = functions

        for name, var in self.variables.iteritems():
            if isinstance(var, Variable) and not isinstance(var, Subexpression):
                if not var.constant:
                    self.nonconstant_values.append((name, var.get_value))
                    if not var.scalar:
                        self.nonconstant_values.append(('_num' + name,
                                                        var.get_len))
                else:
                    try:
                        value = var.get_value()
                    except TypeError:  # A dummy Variable without value
                        continue
                    self.namespace[name] = value
                    # if it is a type that has a length, add a variable called
                    # '_num'+name with its length
                    if not var.scalar:
                        self.namespace['_num' + name] = var.get_len()

    def run(self):
        # generate code
        # TODO: Tidy up this code
        code = {}
        constants = self.constants
        arrays = self.arrays
        functions = self.functions
        print "constants:"
        for const in constants:
            print ', '.join(const)
        print "arrays:"
        for arr in arrays:
            print arr
        print "functions:"
        for func in functions:
            print func
        print "----\n\n"
        if len(constants) > 0:
            code['constants'] = '// CONSTANT DECLARATIONS\n'
            for dtype, k, v in constants:
                code['constants'] += 'const %s %s = %s;\n' % (dtype, k, v)
        # array definitions for Java
        if len(arrays) > 0:
            code['java_array_decl'] = '// JAVA ARRAY DEFINITIONS\n'
            code['java_array_init'] = '// JAVA ARRAY INITIALISATIONS\n'
            code['renderscript_array_decl'] = '// RENDERSCRIPT ARRAY DEFINITIONS\n'
            code['allocation_decl'] = '// ALLOCATION DEFINITIONS\n'
            code['allocation_init'] = '// ALLOCATION INITIALISATIONS\n'
            code['memory_bindings'] = '// MEMORY BINDINGS\n'
            for varname, dtype_spec, N in arrays:
                varname_alloc = varname+"_alloc"
                javatype = dtype_spec['java']
                rstype = dtype_spec['renderscript']
                alloctype = dtype_spec['allocation']
                code['java_array_decl'] += '%s[] %s;\n' % (javatype, varname)
                code['java_array_init'] += '%s = new %s[%s];\n' % (varname,
                                                                   javatype, N)
                code['renderscript_array_decl'] += '%s *%s;\n' % (rstype, varname)
                code['allocation_decl'] += 'Allocation %s;\n' % (varname_alloc)
                code['allocation_init'] += \
                    '%s = Allocation.createSized(mRS, Element.%s(mRS), %s);\n' % (varname_alloc, alloctype, N)
                code['memory_bindings'] += 'mScript.bind_%s(%s);\n' % (varname, varname_alloc)

        # Allocations for input and output of renderscript kernel(s)
        #code += ('in_%s = Allocation.createSized('
        #        'mRS, Element.I32(mRS), %s);\n' % (nrngrp.name, numneurons))
        #code += ('out_%s = Allocation.createSized('
        #        'mRS, Element.I32(mRS), %s);\n' % (nrngrp.name, numneurons))

        if len(code) > 0:
            code['state_updaters'] = '// STATE UPDATERS FOR %s\n' % (self.name)
            code['state_updaters'] += self.code.main+'\n'
        return code

runtime_targets['java'] = JavaCodeObject

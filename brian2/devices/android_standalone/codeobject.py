import os
import numpy

from brian2.codegen.codeobject import CodeObject
from brian2.codegen.templates import Templater
from brian2.codegen.languages import java_lang
from brian2.core.variables import ArrayVariable
from brian2.core.variables import ArrayVariable, Variable, Subexpression

__all__ = ['AndroidStandaloneCodeObject']

global_codeobjects = []

class AndroidStandaloneCodeObject(CodeObject):
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
        # global_codeobjects: temporary - helps keep track of initialised COs
        global_codeobjects.append(self)
        super(AndroidStandaloneCodeObject, self).__init__(code, namespace, variables, name=name)

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
            if isinstance(v, ArrayVariable):
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
        #print "\n\n"+self._name+" ============"
        #print "\tconstants"
        #for con in self.constants:
        #    print "\t\t", con
        #print "\tarrays"
        #for arr in self.arrays:
        #    print "\t\t", arr
        #print "\tnamespace keys"
        #for k in self.namespace.keys():
        #    print "\t\t", k
        constants = self.constants
        arrays = self.arrays
        functions = self.functions
        if len(constants) > 0:
            code['%RENDERSCRIPT CONSTANTS%'] = ''#'// CONSTANT DECLARATIONS\n'
            for dtype, k, v in constants:
                code['%RENDERSCRIPT CONSTANTS%'] += 'const %s %s = %s;\n' % (dtype, k, v)
        # array definitions for Java
        if len(arrays) > 0:
            code['%JAVA ARRAY DECLARATIONS%']    = ''#'// JAVA ARRAY DEFINITIONS\n'
            code['%JAVA ARRAY INITIALISATIONS%'] = ''#'// JAVA ARRAY INITIALISATIONS\n'
            code['%RENDERSCRIPT ARRAYS%']        = ''#'// RENDERSCRIPT ARRAY DEFINITIONS\n'
            code['%ALLOCATION DECLARATIONS%']    = ''#'// ALLOCATION DEFINITIONS\n'
            code['%ALLOCATION INITIALISATIONS%'] = ''#'// ALLOCATION INITIALISATIONS\n'
            code['%MEMORY BINDINGS%']            = ''#'// MEMORY BINDINGS\n'
            for varname, dtype_spec, N in arrays:
                varname_alloc = varname+"_alloc"
                javatype = dtype_spec['java']
                rstype = dtype_spec['renderscript']
                alloctype = dtype_spec['allocation']
                code['%JAVA ARRAY DECLARATIONS%'] += '%s[] %s;\n' % (javatype, varname)
                code['%JAVA ARRAY INITIALISATIONS%'] += '%s = new %s[%s];\n' % (varname,
                                                                   javatype, N)
                code['%RENDERSCRIPT ARRAYS%'] += '%s *%s;\n' % (rstype, varname)
                code['%ALLOCATION DECLARATIONS%'] += 'Allocation %s;\n' % (varname_alloc)
                code['%ALLOCATION INITIALISATIONS%'] += \
                    '%s = Allocation.createSized(mRS, Element.%s(mRS), %s);\n' % (varname_alloc, alloctype, N)
                code['%MEMORY BINDINGS%'] += 'mScript.bind_%s(%s);\n' % (varname, varname_alloc)

        # Allocations for input and output of renderscript kernel(s)
        #code += ('in_%s = Allocation.createSized('
        #        'mRS, Element.I32(mRS), %s);\n' % (nrngrp.name, numneurons))
        #code += ('out_%s = Allocation.createSized('
        #        'mRS, Element.I32(mRS), %s);\n' % (nrngrp.name, numneurons))

        if len(code) > 0:
            code['%STATE UPDATERS%'] = '// STATE UPDATERS FOR %s\n' % (self.name)
            code['%STATE UPDATERS%'] += self.code.main+'\n'
        return code

import functools

from brian2.core.variables import (ArrayVariable, Variable,
                                    AttributeVariable, Subexpression,
                                    StochasticVariable)
from .functions.base import Function
from brian2.core.preferences import brian_prefs
from brian2.core.names import Nameable, find_name
from brian2.utils.logger import get_logger
from .translation import translate
from .runtime.targets import runtime_targets
from brian2.codegen.languages import java_lang

__all__ = ['CodeObject',
           'create_codeobject',
           'get_codeobject_template',
           ]

logger = get_logger(__name__)


def get_default_codeobject_class():
    '''
    Returns the default `CodeObject` class from the preferences.
    '''
    codeobj_class = brian_prefs['codegen.target']
    if isinstance(codeobj_class, str):
        try:
            codeobj_class = runtime_targets[codeobj_class]
        except KeyError:
            raise ValueError("Unknown code generation target: %s, should be "
                             " one of %s"%(codeobj_class, runtime_targets.keys()))
    return codeobj_class


def prepare_namespace(namespace, variables):
    namespace = dict(namespace)
    # Add variables referring to the arrays
    arrays = []
    for value in variables.itervalues():
        if isinstance(value, ArrayVariable):
            arrays.append((value.arrayname, value.get_value()))
    namespace.update(arrays)

    return namespace


def create_codeobject(name, abstract_code, namespace, variables, template_name,
                      indices, variable_indices, codeobj_class=None,
                      template_kwds=None):
    '''
    The following arguments keywords are passed to the template:

    * code_lines coming from translation applied to abstract_code, a list
      of lines of code, given to the template as ``code_lines`` keyword.
    * ``template_kwds`` dict
    * ``kwds`` coming from `translate` function overwrite those in
      ``template_kwds`` (but you should ensure there are no name
      clashes.
    '''

    if template_kwds is None:
        template_kwds = dict()
    else:
        template_kwds = template_kwds.copy()

    if codeobj_class is None:
        codeobj_class = get_default_codeobject_class()

    template = get_codeobject_template(template_name,
                                       codeobj_class=codeobj_class)

    namespace = prepare_namespace(namespace, variables)

    logger.debug(name + " abstract code:\n" + abstract_code)
    iterate_all = template.iterate_all
    innercode, kwds = translate(abstract_code, variables, namespace,
                                dtype=brian_prefs['core.default_scalar_dtype'],
                                language=codeobj_class.language,
                                variable_indices=variable_indices,
                                iterate_all=iterate_all)
    template_kwds.update(kwds)
    logger.debug(name + " inner code:\n" + str(innercode))

    name = find_name(name)

    code = template(innercode, **template_kwds)
    logger.debug(name + " code:\n" + str(code))

    variables.update(indices)
    codeobj = codeobj_class(code, namespace, variables, name=name)
    #codeobj.compile()
    return codeobj


def get_codeobject_template(name, codeobj_class=None):
    '''
    Returns the `CodeObject` template ``name`` from the default or given class.
    '''
    if codeobj_class is None:
        codeobj_class = get_default_codeobject_class()
    return getattr(codeobj_class.templater, name)


class CodeObject(Nameable):
    '''
    Executable code object.

    The ``code`` can either be a string or a
    `brian2.codegen.templates.MultiTemplate`.

    After initialisation, the code is compiled with the given namespace
    using ``code.compile(namespace)``.

    Calling ``code(key1=val1, key2=val2)`` executes the code with the given
    variables inserted into the namespace.
    '''

    #: The `Language` used by this `CodeObject`
    language = None

    def __init__(self, code, namespace, variables, name='codeobject*'):
        Nameable.__init__(self, name=name)
        self.code = code
        constants = []
        arrays = []
        functions = []
        for k, v in namespace.items():
            if isinstance(v, float):
                # TODO: Use the language submodule to translate
                dtype = "float"
                constants.append((dtype, k, repr(v)+'f'))
            elif isinstance(v, int):
                dtype = "int"
                constants.append((dtype, k, repr(v)))
            elif hasattr(v, '__call__'):
                functions.append((k, v))

        for k, v in variables.items():
            if isinstance (v, ArrayVariable):
                dtype_spec = java_lang.java_data_type(v.dtype)
                # TODO: Perhaps it would be more convenient as a dictionary?
                arrays.append((k, dtype_spec, len(v.value)))
        # NOTE: self.namespace structure is inconsistent with the general way
        # namespaces are defined. Is this an issue?
        self.namespace = {
                'arrays' : arrays,
                'constants' : constants,
                'functions' : functions
                }

        '''
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
        '''

    def get_compile_methods(self, variables):
        meths = []
        for var, var in variables.items():
            if isinstance(var, Function):
                meths.append(functools.partial(var.on_compile,
                                               language=self.language,
                                               var=var))
        return meths

    def compile(self):
        for meth in self.compile_methods:
            meth(self.namespace)

    def __call__(self):
        # generate code
        print self.name+" is being called"
        code = ''
        constants = self.namespace['constants']
        arrays = self.namespace['arrays']
        functions = self.namespace['functions']
        code += '\n// CONSTANT DECLARATIONS\n'
        for dtype, k, v in constants:
            if isinstance(v, float):
                code += ('const double %s = %s;\n' % (k, repr(v)))
            elif isinstance(v, int):
                code += ('const int %s = %s;\n' % (k, repr(v)))


        # TODO: The following fout loops can be combined in one
        # where each statement in the loop prints to the appropriate file

        # array definitions for Java
        code += '\n// JAVA ARRAY DEFINITIONS\n'
        for varname, dtype_spec, N in arrays:
            javatype = dtype_spec['java']
            code += '%s %s = new %s[%i];\n' % (javatype,
                                            varname,
                                            javatype,
                                            N)

        # array definitions for Renderscript
        code += '\n// RENDERSCRIPT ARRAY DEFINITIONS\n'
        for varname, dtype_spec, N in arrays:
            rstype = dtype_spec['renderscript']
            code += '%s *%s;\n' % (rstype, varname)

        # array definitions for Allocations
        code += '\n// ALLOCATION DEFINITIONS\n'
        for varname, dtype_spec, N in arrays:
            alloctype = dtype_spec['allocation']
            code += ('Allocation %s = Allocation.createSized(mRS, '
                    'Element.%s(mRS), %i);\n'
                    % (varname, alloctype, N))

        # Allocations for input and output of renderscript kernel(s)
        #code += ('in_%s_rs = Allocation.createSized('
        #        'mRS, Element.I32(mRS), %s);\n' % (nrngrp.name, numneurons))
        #code += ('out_%s_rs = Allocation.createSized('
        #        'mRS, Element.I32(mRS), %s);\n' % (nrngrp.name, numneurons))

        # binding Java arrays to Renderscript via Allocations
        code += '\n// MEMORY BINDING\n'
        for varname, dtype_spec, N in arrays:
            code += 'mScript.bind%s(%s_rs);\n' % (varname, varname)
        # Allocations for input and output
        code += '\n// STATE UPDATERS FOR %s\n' % (self.name)
        code += self.code+'\n'
        return code



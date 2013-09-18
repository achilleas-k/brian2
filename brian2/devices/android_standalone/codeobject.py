import os
import numpy

from brian2.codegen.codeobject import CodeObject
from brian2.codegen.templates import Templater
from brian2.codegen.languages import java_lang
from brian2.core.variables import ArrayVariable
from brian2.core.variables import ArrayVariable, Variable, Subexpression

__all__ = ['AndroidCodeObject']

global_codeobjects = []

class AndroidCodeObject(CodeObject):
    '''
    Java code object

    The ``code`` should be a `~brian2.codegen.languages.templates.MultiTemplate`
    object with two macros defined, ``main`` (for the main loop code) and
    ``support_code`` for any support code (e.g. function definitions).
    '''
    templater = Templater(os.path.join(os.path.split(__file__)[0],
                                       'templates'))
    language = java_lang.JavaLanguage()

    def __init__(self, owner, code, namespace, variables, name='codeobject*'):
        # global_codeobjects: temporary - helps keep track of initialised COs
        global_codeobjects.append(self)
        super(AndroidCodeObject, self).__init__(owner, code, namespace, variables, name=name)

    def variables_to_namespace(self):
        # We only copy constant scalar values to the namespace here
        for varname, var in self.variables.iteritems():
            if var.constant and var.scalar:
                self.namespace[varname] = var.get_value()

    def run(self):
        raise RuntimeError("Cannot run in Android standalone mode")


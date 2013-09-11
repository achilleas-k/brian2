import os
import numpy

from brian2.codegen.codeobject import CodeObject
from brian2.codegen.templates import Templater
from brian2.codegen.languages.java_lang import JavaLanguage

__all__ = ['AndroidStandaloneCodeObject']


class AndroidStandaloneCodeObject(CodeObject):
    '''
    C++ standalone code object
    
    The ``code`` should be a `~brian2.codegen.languages.templates.MultiTemplate`
    object with two macros defined, ``main`` (for the main loop code) and
    ``support_code`` for any support code (e.g. function definitions).
    '''
    templater = Templater(os.path.join(os.path.split(__file__)[0],
                                       'templates'))
    language = JavaLanguage()

    def run(self):
        raise RuntimeError("Cannot run in C++ standalone mode")

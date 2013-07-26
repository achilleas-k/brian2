import os

from ...codeobject import CodeObject
from ...templates import Templater
from ...languages.java_lang import JavaLanguage
from ..targets import runtime_targets

from brian2.core.preferences import brian_prefs, BrianPreference

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
    Weave code object
    
    The ``code`` should be a `~brian2.codegen.languages.templates.MultiTemplate`
    object with two macros defined, ``main`` (for the main loop code) and
    ``support_code`` for any support code (e.g. function definitions).
    '''
    templater = Templater(os.path.join(os.path.split(__file__)[0],
                                       'templates'))
    language = JavaLanguage()

    def __init__(self, code, namespace, specifiers):
        super(JavaCodeObject, self).__init__(code, namespace, specifiers)
        self.compiler = brian_prefs['codegen.runtime.java.compiler']
        self.extra_compile_args = brian_prefs['codegen.runtime.java.extra_compile_args']

    def run(self):
        return java.inline(self.code.main, self.namespace.keys(),
                            local_dict=self.namespace,
                            support_code=self.code.support_code,
                            compiler=self.compiler,
                            extra_compile_args=self.extra_compile_args)

runtime_targets['java'] = JavaCodeObject

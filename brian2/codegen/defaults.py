from languages.python import PythonLanguage

__all__ = ['get_default_language',
           'set_default_language',
           ]

default_language = PythonLanguage()

def set_default_language(lang):
    global default_language
    default_language = lang
    
def get_default_language():
    return default_language

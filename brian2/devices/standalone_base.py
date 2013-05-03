'''
A common base package for standalone versions of Brian. Handles creating an
output directory, all the object types are mapped to code generation calls,
etc.

Ideas and questions
-------------------

* Have a global variable that defines whether or not objects should allocate
  memory or not, deactivated for devices which will manage their own memory.
  Requires that whenever we work with a Brian object we have to test if the
  memory has been allocated, which might be annoying.
'''

import brian2
import os
import fnmatch
from brian2.devices.methodlogger import method_logger, MethodCall
from brian2.devices.functionlogger import function_logger, FunctionCall

__all__ = [# Package classes and functions
           'Implementation', 'Handler', 'MethodHandler',
           ]

class Handler(object):
    def __init__(self, implementation):
        self.implementation = implementation
        
class MethodHandler(Handler):
    def __call__(self, proc):
        if proc.methname=='__init__':
            self.init(proc)
        else:
            getattr(self, proc.methname)(proc)


class Implementation(object):
    '''
    The base class for all standalone Brian implementations.
    '''
    class_handlers = []
    function_handlers = []

    def __init__(self):
        self.procedural_order = []
        self.handlers = {}
        self.set_output_directory()

    def registration(self, all, ns):
        '''
        Handles registration of method and function call handlers
        
        Must be called from the implementation module with its ``__all__``
        and ``globals()``.
        
        Parameters
        ----------
        
        all : list
            The ``__all__`` list of the implementation module.
        ns : dict
            The ``globals()`` of the implementation module.
        '''
        for handler in self.class_handlers:
            self.register_class(handler.handle_class, all, ns,
                                methnames=handler.method_names)
            self.handlers[handler.handle_class] = handler(self)
        for handler in self.function_handlers:
            self.register_function(handler.handle_function, all, ns,
                                   runit=handler.runit)
            self.handlers[handler.handle_function] = handler(self)

    def register_class(self, cls, all, ns, methnames=None):
        '''
        Register a class to log its method calls into `procedural_order`
        
        Inserts the newly created class, derived from the original class, into
        the global namespace of the calling module, adds it to the ``__all__``
        list so that it will be imported when that module is imported.
        
        Parameters
        ----------
        
        cls : class
            The class to log method calls
        all : list
            The ``__all__`` list of the module.
        ns : dict
            The ``globals()`` dict of the module.
        methnames : None or set
            The set of method names to log.
        '''
        all.append(cls.__name__)
        newcls = method_logger(cls, self.procedural_order, methnames=methnames)
        ns[cls.__name__] = newcls
        
    def register_function(self, func, all, ns, runit=True):
        '''
        Register a function to log its calls into `procedural_order`

        Inserts the newly created function into
        the global namespace of the calling module, adds it to the ``__all__``
        list so that it will be imported when that module is imported.

        Parameters
        ----------
        
        func : function
            The function whose calls to log.
        all : list
            The ``__all__`` list of the module.
        ns : dict
            The ``globals()`` dict of the module.
        runit : bool
            Whether or not to run the function.
        '''
        all.append(func.__name__)
        newfunc = function_logger(func, self.procedural_order, runit=runit)
        ns[func.__name__] = newfunc

    def ensure_directory(self, d):
        '''
        Ensures that a directory exists, and returns the path.
        '''
        if not os.path.exists(d):
            os.makedirs(d)
        return d
    
    def ensure_directory_of_file(self, f):
        '''
        Ensures that a directory exists for filename to go in (creates if
        necessary), and returns the directory path.
        '''
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)
        return d
    
    def copy_directory(self, source, target):
        '''
        Copies directory source to target.
        '''
        sourcebase = os.path.normpath(source)+os.path.sep
        for root, dirnames, filenames in os.walk(source):
            for filename in filenames:
                fullname = os.path.normpath(os.path.join(root, filename))
                relname = fullname.replace(sourcebase, '')
                tgtname = os.path.join(target, relname)
                self.ensure_directory_of_file(tgtname)
                open(tgtname, 'w').write(open(fullname).read())
                
    def recursive_filename_match_relative(self, source, pattern):
        '''
        Returns all filename in directory source or subdirectories matching pattern.
        
        Returns a list of filenames relative to source.
        '''
        sourcebase = os.path.normpath(source)+os.path.sep
        names = []
        for root, dirnames, filenames in os.walk(source):
            for filename in fnmatch.filter(filenames, pattern):
                fullname = os.path.normpath(os.path.join(root, filename))
                relname = fullname.replace(sourcebase, '')
                names.append(relname)
        return names
    
    def set_output_directory(self, path=None):
        if path is None:
            path = 'output'
        self.path = path
    
    def ensure_output_directory(self):
        self.ensure_directory(self.path)
        
    def build(self):
        self.ensure_output_directory()
        with open(os.path.join(self.path, 'main.txt'), 'w') as file:
            for obj, f, args, kwds in self.procedural_order:
                proc = self.get_procedure_representation(obj, f, args, kwds)
                if obj is not None:
                    definition = obj.name+' = '+proc
                    proc = "create('%s') # %s"%(obj.name, proc)
                    with open(os.path.join(self.path, obj.name+'.txt'), 'w') as file2:
                        file2.write(definition+'\n')
                file.write(proc+'\n')

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

__all__ = [# Package classes and functions
           'Implementation',
           # Original Brian objects and functions
           'run', 'NeuronGroup',
           # Device specific objects and functions
           'build',
           ]

def make_procedural(original_func, runit=True):
    def new_func(self, *args, **kwds):
        if runit:
            obj = original_func(*args, **kwds)
            self.procedural_order.append((obj, original_func, args, kwds))
            return obj
        else:
            self.procedural_order.append((None, original_func, args, kwds))
    return new_func

class Implementation(object):
    '''
    The base class for all standalone Brian implementations.
    '''
    def __init__(self):
        self.procedural_order = []
        self.set_output_directory()

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
        
    run = make_procedural(brian2.run, runit=False)
    NeuronGroup = make_procedural(brian2.NeuronGroup)

    def get_procedure_representation(self, obj, f, args, kwds):
        argstr = ', '.join(repr(arg) for arg in args)
        kwdstr = ', '.join(k+'='+repr(v) for k, v in kwds.items())
        m = []
        if argstr:
            m.append(argstr)
        if kwdstr:
            m.append(kwdstr)
        proc = '%s(%s)'%(f.__name__, ', '.join(m))
        return proc
    
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

implementation = Implementation()

run = implementation.run
NeuronGroup = implementation.NeuronGroup
build = implementation.build

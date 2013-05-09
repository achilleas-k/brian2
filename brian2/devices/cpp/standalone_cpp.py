'''
Notes on C++ implementation of Brian
====================================

For the most part, the C++ implementation follows the Python implementation.

The static part (that doesn't make use of code generation) is stored in the
``cpp_code/brianlib`` directory. The templates are stored in
``cpp_code/templates``.

Directory structure
-------------------

In both ``cpp_code/brianlib`` and ``cpp_code/templates`` there is a directory
structure and filenames that mimic, where possible, the Python package structure
and module names.

When an output project is generated, the ``brianlib`` directory will be copied
directly to ``output/brianlib``. Each object created via a template is inserted
into the ``output/objects`` directory in a flat manner.

Static Brian library
--------------------

In order to mimic importing a package consisting of multiple modules, a header
file can be created that imports all the "package" header files. For example,
the units package has two modules allunits and stdunits (and some others we
ignore here). We therefore get the following directory structure::

    units/allunits.h
    units/stdunits.h
    units.h
    
Where here the ``units.h`` file consists simply of::

    #include "units/allunits.h"
    #include "units/stdunits.h"
    
Templates
---------

Templates are stored in Jinja format.

Each template class derives from a
class in ``brianlib`` and adds the minimal amount of functionality possible to
that class. As much as possible should be put in the static library.

Each instance of a templated class should be given a class name ``C_name``
where ``name`` is replaced by the object's unique name. The object ``name``is
defined in the ``main()`` function.

Differences between Python version and C++ version
--------------------------------------------------

Units
^^^^^

There is no unit class in the C++ version, rather everything is of ``scalar``
type, which can be either ``float`` or ``double``. This is defined in the
``briantypes.h`` header file. Units are simply constant values (e.g.
``ms=0.001``.

Nameable
^^^^^^^^

There is no `Nameable` base class, because the name of each object is the
name of the (global) variable.

Scheduler
^^^^^^^^^

This class has been removed since it was only used for user-friendliness which
isn't a problem for the generated code.
'''
import os
import glob
from collections import defaultdict
import inspect

from jinja2 import Template

import numpy

import brian2
from brian2.devices.standalone_base import (Implementation, Handler,
                                            MethodHandler)
from brian2.codegen import set_default_language
from brian2.codegen.languages.cpp import CPPLanguage
from brian2.devices.methodlogger import method_logger, MethodCall
from brian2.devices.functionlogger import function_logger, FunctionCall

__all__ = [# Package classes and functions
           'CPPImplementation',
           'CPPMethodHandler',
           # Device specific objects and functions
           'build', 'insert_code',
           ]

set_default_language(CPPLanguage())

curdir, _ = os.path.split(__file__)
codedir = os.path.join(curdir, 'cpp_code')
brianlibdir = os.path.join(codedir, 'brianlib')
templatedir = os.path.join(codedir, 'templates')

class CPPMethodHandlerMethod(object):
    '''
    This class is used for runtime generated methods for the `CPPMethodHandler` class.
    
    It is called with the ``proc`` `MethodCall` argument by `CPPImplementation`,
    and handles inserting lines into the main.cpp file and creating templated
    files corresponding to each object. See `CPPMethodHandler` for more details.
    
    When called with ``proc`` it finds a template file by checking
    the original `CPPMethodHandler` class attribute with the same name. If it
    is a string, it uses it directly. If it is a method, it uses the string
    returned by the method.

    This template will be rendered with the namespace defined by
    ``proc.__dict__`` and (optionally, if one exists) the namespace returned by
    ``handler._namespace(proc)``. The rendered template will be inserted
    directly into the main.cpp file. If the method is the
    ``__init__`` method, then it will additionally search for the following
    template files::
    
        templatedir/basename.cpp
        templatedir/basename.h
    
    Parameters
    ----------
    
    handler : MethodHandler
        The main handler class which this method will be attached to.
    name : str
        The name of the method.
    orig : method or str
        The original method (if there was one), which can be used to do extra
        work beyond what the automatic handling does. Or a string in Jinja
        format with text to be inserted into ``main.cpp``.
    basename : str
        The base filename of template definitions for this class/method.
    '''
    def __init__(self, handler, name, orig, basename):
        self.handler = handler
        self.implementation = handler.implementation
        self.name = name
        self.orig = orig
        self.basename = basename
    def __call__(self, proc):
        # Call the original Handler's method first if it has one, it may
        # raise errors or modify proc.
        if isinstance(self.orig, str):
            tmpstr = self.orig
        else:
            tmpstr = self.orig(proc)
        ns = proc.__dict__.copy()
        if hasattr(self.handler, '_namespace'):
            ns.update(self.handler._namespace(proc))
        # Try to load the file which should be inserted into main.cpp
        if self.name=='init':
            dotname = '__init__'
        else:
            dotname = self.name
        # Apply the template
        tmp = Template(tmpstr)
        outstr = tmp.render(**ns)
        self.implementation.procedure_lines.append(outstr)
        # If this is the init method, try to load the class template
        if dotname=='__init__':
            for ext in ['cpp', 'h']:
                tmpfn = os.path.join(templatedir, self.basename+'.'+ext)
                if os.path.exists(tmpfn):
                    tmpstr = open(tmpfn, 'r').read()
                    tmp = (os.path.join('templates', self.basename+'.'+ext),
                           'objects/'+proc.obj.name+'.'+ext,
                           ns)
                    self.implementation.templates.append(tmp)
                    if ext=='h':
                        self.implementation.additional_headers.append('objects/'+proc.obj.name+'.h')
                    

class CPPMethodHandler(MethodHandler):
    '''
    Handles translation of method calls on objects into standalone code.
    
    This class is designed to be derived from. You should define two class
    attributes:
    
    ``handle_class`` : class
        The Brian class which is being handled by this object.
    ``method_names`` : dict
        A dictionary of pairs ``(name, runit)`` giving the names of the methods
        to be handled, and whether or not the method should actually be called
        or only translated into code. For example ``run`` methods shouldn't
        usually be called, but other methods might.
        
    The class will automatically handle translation of code in the following
    way. It computes a base filename for template files, this base filename
    consists of the source filename of the Brian class relative to the
    Brian package directory, e.g. for `NeuronGroup` it would be
    ``groups/neurongroup``. The full base name is then::
    
        basefilename/classname
        
    So for `NeuronGroup` it would be ``groups/neurongroup/NeuronGroup``.
    Now all the template files will be stored in the template directory,
    followed by this name, followed by various values. If you want to provide
    a full template for the whole class (with various methods, etc.) then
    create files::
    
        templates/basename.cpp
        templates/basename.h
        
    If you want to provide code that will be inserted into the ``main.cpp``
    at the place corresponding to the method call, then create a class
    attribute with the string (in Jinja format) or a method taking an argument
    ``proc`` that returns a string (in Jinja format).
        
    See `CPPMethodHandlerMethod` for more details.
    
    By default, the template files are considered as Jinja template files,
    with a namespace based on the dict of the `MethodCall` object. If in
    addition the `CPPMethodHandler` class defines a ``_namespace(proc)`` method
    then the namespace returned by this will be added to the namespace used by
    Jinja to render it. The ``proc`` argument is the `MethodCall` object.
    
    Parameters
    ----------
    
    implementation : CPPImplementation
        The main `CPPImplementation` object (provided automatically).
    '''
    def __init__(self, implementation):
        MethodHandler.__init__(self, implementation)
        # Find the base file name for templates, etc.
        classfilename = inspect.getsourcefile(self.handle_class)
        brian2filename = inspect.getsourcefile(brian2).replace('__init__.py', '')
        # remove the brian2 common part and the .py at the end
        self.basename = classfilename.replace(brian2filename, '')[:-3]+'/'+self.handle_class.__name__
        # Set up methods
        for name in self.method_names.keys():
            if name=='__init__':
                name = 'init'
            # We keep the currently existing method because it might do stuff
            # like adding things to proc, or raising errors, that cannot be
            # handled automatically with template files.
            orig = getattr(self, name, None)
            setattr(self, name, CPPMethodHandlerMethod(self, name, orig,
                                                        self.basename))


# TODO: make RunHandler work like CPPMethodHandler
class RunHandler(Handler):
    handle_function = brian2.run
    runit = False
    def __call__(self, proc):
        self.implementation.procedure_lines.append(proc.call_representation)

        
# TODO: add methods to add code to main.cpp and to add templates to render,
# this will make it all much clearer than directly adding to .procedure_lines,
# and so forth.
class CPPImplementation(Implementation):
    function_handlers = [RunHandler]
    
    def __init__(self):
        Implementation.__init__(self)
        self.find_class_handlers()
        self.registration(__all__, globals())
        
    def find_class_handlers(self):
        self.class_handlers = []
        for root, dirnames, filenames in os.walk(templatedir):
            for filename in filenames:
                if not filename.endswith('.py'):
                    continue
                fullname = os.path.normpath(os.path.join(root, filename))
                ns = {}
                # TODO: improve this by importing using imp.load_source?
                execfile(fullname, ns)
                for k, v in ns.items():
                    if k.startswith('_'):
                        continue
                    if inspect.isclass(v) and issubclass(v, CPPMethodHandler) and v is not CPPMethodHandler:
                        self.class_handlers.append(v)
                        
    def copy_brianlib_files(self):
        self.copy_directory(brianlibdir,
                            os.path.join(self.path, 'brianlib'))
                                
    def build(self, run=False):
        self.ensure_output_directory()
        self.copy_brianlib_files()
        
        # Templates for main.cpp use these
        self.procedure_lines = procedure_lines = []
        self.additional_headers = []  
        objects = set()
        ns = {'procedure_lines': procedure_lines,
              'objects': objects,
              'headers': self.additional_headers,
              'defaultclock': brian2.defaultclock,
              }
        self.templates = templates = [('templates/main.cpp', 'main.cpp', ns)]
        
        # Go through procedures generating templates for referenced objects
        for proc in self.procedural_order:
            for v in [getattr(proc, 'returnval', None), getattr(proc, 'obj', None)]:
                if isinstance(v, brian2.Nameable):
                    objects.add(v)
            if isinstance(proc, str):
                self.procedure_lines.append(proc)
            elif proc.handlekey in self.handlers:
                self.handlers[proc.handlekey](proc)
            else:
                raise Exception("What to do with this? "+repr(proc))

        # Write out templated files
        for inputname, outputname, ns in templates:
            tmpstr = open(os.path.join(codedir, inputname)).read()
            tmp = Template(tmpstr)
            outstr = tmp.render(**ns)
            outfname = os.path.join(self.path, outputname)
            self.ensure_directory_of_file(outfname) 
            open(outfname, 'w').write(outstr)
            
        # Generate a makefile
        # TODO: make a cleaner makefile
        cpp_files = self.recursive_filename_match_relative(self.path, '*.cpp')
        cpp_files = [f.replace('\\', '/') for f in cpp_files]
        open(os.path.join(self.path, 'makefile'), 'w').write('''
all:
\tg++ -I. -std=c++0x {names} -o runsim
        '''.format(names=' '.join(cpp_files)))
        
        if run:
            # Try to make and run the project
            cwd = os.getcwd()
            os.chdir(self.path)
            print '********** BUILDING PROJECT ************'
            print
            rv = os.system('make')
            if rv:
                os.chdir(cwd)
                raise RuntimeError("Error building project.")
            print
            print '********** RUNNING PROJECT *************'
            print
            rv = os.system('runsim')
            os.chdir(cwd)
            if rv:
                raise RuntimeError("Error running project.")
            
        
    def insert_code(self, code):
        '''
        Inserts C++ code directly into the main function.
        '''
        self.procedural_order.append(code)

implementation = CPPImplementation()

build = implementation.build
insert_code = implementation.insert_code

if __name__=='__main__':
    print templatedir

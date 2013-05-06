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
           # Device specific objects and functions
           'build', 'insert_code',
           ]

set_default_language(CPPLanguage())

curdir, _ = os.path.split(__file__)
codedir = os.path.join(curdir, 'cpp_code')
brianlibdir = os.path.join(codedir, 'brianlib')
templatedir = os.path.join(codedir, 'templates')

class NeuronGroupHandler(MethodHandler):
    handle_class = brian2.NeuronGroup
    method_names = {'__init__':True,
                    'set_state_':True, 'set_state':True,
                    }
    def _get_template_namespace(self, obj):
        ns = {'name': obj.name,
              'variables':obj.arrays.keys(),
              'num_neurons':len(obj),
              'state_update_code':obj.state_updater.codeobj.code['%MAIN%'],
              'dt':float(obj.clock.dt),
              }
        return ns
    
    def init(self, proc):
        obj = proc.obj
        ns = self._get_template_namespace(obj)
        tmp_cpp = ('templates/groups/neurongroup.cpp',
                   'objects/'+obj.name+'.cpp',
                   ns)
        tmp_h = ('templates/groups/neurongroup.h',
                 'objects/'+obj.name+'.h',
                 ns)
        self.implementation.templates.extend([tmp_cpp, tmp_h])
        self.implementation.additional_headers.append('objects/'+obj.name+'.h')
        initobj_str = 'C_{name} {name}("{when}", {order}, {clock}, {N});'.format(
                        name=obj.name, when=obj.when, order=obj.order,
                       clock=obj.clock.name, N=len(obj),
                       )
        self.implementation.procedure_lines.append(initobj_str)
        
    def set_state(self, proc):
        name, val = proc.args
        if isinstance(val, (str, numpy.ndarray)):
            raise ValueError("Can only handle scalar values for now.")
        val = float(val)
        line = '{obj}.set_state("{var}", {val});'.format(obj=proc.objname,
                                                       var=name, val=val)
        self.implementation.procedure_lines.append(line)
    set_state_ = set_state


class NetworkHandler(MethodHandler):
    handle_class = brian2.Network
    method_names = {'__init__': True,
                    'run': False,
                    }
    def init(self, proc):
        code = 'Network {name};\n'.format(name=proc.obj.name)
        for obj in proc.args:
            code += '{name}.add({obj_name});\n'.format(name=proc.obj.name,
                                                       obj_name=obj.name)
        self.implementation.procedure_lines.append(code)
    
    def run(self, proc):
        code = '{name}.run({duration})'.format(name=proc.obj.name,
                                               duration=repr(proc.args[0]))
        self.implementation.procedure_lines.append(code)


class RunHandler(Handler):
    handle_function = brian2.run
    runit = False
    def __call__(self, proc):
        self.implementation.procedure_lines.append(proc.call_representation)

        
class CPPImplementation(Implementation):
    class_handlers = [NeuronGroupHandler, NetworkHandler]
    function_handlers = [RunHandler]
    
    def __init__(self):
        Implementation.__init__(self)
        self.registration(__all__, globals())
                        
    def copy_brianlib_files(self):
        self.copy_directory(brianlibdir,
                            os.path.join(self.path, 'brianlib'))
                                
    def build(self):
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

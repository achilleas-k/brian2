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

import brian2
from brian2.devices.standalone_base import Implementation
from brian2.codegen import set_default_language
from brian2.codegen.languages.cpp import CPPLanguage
from brian2.devices.methodlogger import method_logger, MethodCall
from brian2.devices.functionlogger import function_logger, FunctionCall

__all__ = [# Package classes and functions
           'CPPImplementation',
           # Device specific objects and functions
           'build',
           ]

set_default_language(CPPLanguage())

curdir, _ = os.path.split(__file__)
codedir = os.path.join(curdir, 'cpp_code')
brianlibdir = os.path.join(codedir, 'brianlib')
templatedir = os.path.join(codedir, 'templates')

class CPPImplementation(Implementation):
    def __init__(self):
        Implementation.__init__(self)
        self.register_class(brian2.NeuronGroup, __all__, globals(),
                            methnames=set(['__init__',
                                           #'set_state_', 'state_',
                                           #'set_state', 'state',
                                           ]),
                            )
        self.register_function(brian2.run, __all__, globals(), runit=False)
                
    def copy_brianlib_files(self):
        self.copy_directory(brianlibdir,
                            os.path.join(self.path, 'brianlib'))
            
    def template_NeuronGroup(self, obj, f, args, kwds):
        ns = {'name': obj.name,
              'variables':obj.arrays.keys(),
              'num_neurons':len(obj),
              'state_update_code':obj.state_updater.codeobj.code['%MAIN%'],
              'dt':float(obj.clock.dt),
              }
        tmp_cpp = ('templates/groups/neurongroup.cpp',
                   'objects/'+obj.name+'.cpp',
                   ns)
        tmp_h = ('templates/groups/neurongroup.h',
                 'objects/'+obj.name+'.h',
                 ns)
        self.templates.extend([tmp_cpp, tmp_h])
        proc = self.get_procedure_representation(obj, f, args, kwds)
        initobj_str = 'C_{name} {name}("{when}", {order}, {clock}); /* {proc} */'.format(
            name=obj.name, when=obj.when, order=obj.order, clock=obj.clock.name,
            proc=proc)
        self.procedure_lines.append(initobj_str)
                    
    def build(self):
        self.ensure_output_directory()
        self.copy_brianlib_files()
        
        # Templates for main.cpp use these
        self.procedure_lines = procedure_lines = []
        objects = []
        ns = {'procedure_lines': procedure_lines,
              'objects': objects,
              'defaultclock': brian2.defaultclock,
              }
        self.templates = templates = [('templates/main.cpp', 'main.cpp', ns)]        
        
        # Go through procedures generating templates for referenced objects
        for proc in self.procedural_order:
            if isinstance(proc, MethodCall) and proc.objclass is brian2.NeuronGroup and proc.methname=='__init__':
                self.template_NeuronGroup(proc.obj, brian2.NeuronGroup,
                                          proc.args, proc.kwds)
                objects.append(proc.obj)
            elif isinstance(proc, FunctionCall):
                self.procedure_lines.append(proc.call_representation)
            else:
                raise Exception("Don't know what to do with "+repr(proc))
            
            if proc.returnval is not None:
                objects.append(proc.returnval)

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
\tg++ -I. {names} -o runsim
        '''.format(names=' '.join(cpp_files)))

implementation = CPPImplementation()

build = implementation.build

if __name__=='__main__':
    print templatedir

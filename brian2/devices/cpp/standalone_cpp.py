import os
import glob
from collections import defaultdict

from jinja2 import Template

import brian2
from brian2.devices.standalone_base import Implementation

__all__ = [# Package classes and functions
           'CPPImplementation',
           # Original Brian objects and functions
           'run', 'NeuronGroup',
           # Device specific objects and functions
           'build',
           ]

curdir, _ = os.path.split(__file__)
templatedir = os.path.join(curdir, 'templates')

class CPPImplementation(Implementation):
    def copy_brianlib_files(self):
        # This is unnecessarily hacky and could be done much more cleanly
        # using shutils
        if not os.path.exists(os.path.join(self.path, 'brianlib')):
            os.mkdir(os.path.join(self.path, 'brianlib'))
        for file in glob.glob(os.path.join(templatedir, 'brianlib', '*.*')):
            _, fname = os.path.split(file)
            open(os.path.join(self.path, 'brianlib', fname), 'w').write(open(file).read())
            
    def template_NeuronGroup(self, obj, f, args, kwds, templates, procedure_lines):
        ns = {'name': obj.name}
        tmp_cpp = ('neurongroup.cpp', obj.name+'.cpp', ns)
        tmp_h = ('neurongroup.h', obj.name+'.h', ns)
        templates.extend([tmp_cpp, tmp_h])
        proc = self.get_procedure_representation(obj, f, args, kwds)
        initobj_str = '%s._init(); /* %s */\n'%(obj.name, proc)
        procedure_lines.append(initobj_str)
                    
    def build(self):
        self.ensure_output_directory()
        self.copy_brianlib_files()
        
        # Templates for main.cpp use these
        procedure_lines = []
        objects = []
        ns = {'procedure_lines': procedure_lines,
              'objects': objects,
              }
        templates = [('main.cpp', 'main.cpp', ns)]        
        
        # Go through procedures generating templates for referenced objects
        for obj, f, args, kwds in self.procedural_order:
            proc = self.get_procedure_representation(obj, f, args, kwds)
            
            if obj is not None:
                objects.append(obj)
                
            if obj is None:
                procedure_lines.append(proc)
            elif isinstance(obj, brian2.NeuronGroup):
                self.template_NeuronGroup(obj, f, args, kwds,
                                          templates, procedure_lines)
            else:
                raise Exception("object unknown")

        # Write out templated files
        for inputname, outputname, ns in templates:
            tmpstr = open(os.path.join(templatedir, inputname)).read()
            tmp = Template(tmpstr)
            outstr = tmp.render(**ns)
            open(os.path.join(self.path, outputname), 'w').write(outstr)
            

implementation = CPPImplementation()

run = implementation.run
NeuronGroup = implementation.NeuronGroup
build = implementation.build

if __name__=='__main__':
    print templatedir

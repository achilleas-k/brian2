import brian2
from brian2.devices.standalone_base import Implementation
import os
import glob
from collections import defaultdict

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
            
    def template_NeuronGroup(self, obj, f, args, kwds, templates, templatefiles):
        proc = self.get_procedure_representation(obj, f, args, kwds)
        name_cpp = '%s.cpp'%obj.name
        name_h = '%s.h'%obj.name
        createobj_str = 'C_%s %s();\n'%(obj.name, obj.name)
        initobj_str = '%s._init(); /* %s */\n'%(obj.name, proc)
        include_str = '#include "%s.h"\n'%obj.name
        namedef_str = '#define CLASSNAME C_%s\n#define OBJNAME %s\n'%(obj.name, obj.name)
        templates['main.cpp']['PROCEDURES'] += initobj_str
        templates['main.cpp']['INCLUDES'] += include_str
        templatefiles[name_cpp] = 'neurongroup.cpp'
        templatefiles[name_h] = 'neurongroup.h'
        templates[name_h]['NAMEDEFS'] = namedef_str
        templates[name_cpp]['INCLUDE_HEADER'] = include_str
                    
    def build(self):
        self.ensure_output_directory()
        self.copy_brianlib_files()
        
        # Generate the templated files
        templatefiles = {}
        templates = defaultdict(lambda: defaultdict(str))
        maintemplate = templates['main.cpp']
        templatefiles['main.cpp'] = 'main.cpp'
        for obj, f, args, kwds in self.procedural_order:
            proc = self.get_procedure_representation(obj, f, args, kwds)
            if obj is None:
                maintemplate['PROCEDURES'] += proc+';\n'
            elif isinstance(obj, brian2.NeuronGroup):
                self.template_NeuronGroup(obj, f, args, kwds, templates,
                                          templatefiles)
            else:
                raise Exception("object unknown")

        # Write out the templated files
        for name, template in templates.items():
            tmpstr = open(os.path.join(templatedir, templatefiles[name])).read()
            for k, v in template.items():
                tmpstr = tmpstr.replace('//%'+k, v)
            open(os.path.join(self.path, name), 'w').write(tmpstr)
            

implementation = CPPImplementation()

run = implementation.run
NeuronGroup = implementation.NeuronGroup
build = implementation.build

if __name__=='__main__':
    print templatedir
import numpy
import os
import inspect
from collections import defaultdict

from brian2.units import second
from brian2.core.clocks import defaultclock
from brian2.devices.device import Device, set_device, all_devices
from brian2.core.preferences import brian_prefs
from brian2.core.variables import *
from brian2.utils.filetools import copy_directory
from brian2.utils.stringtools import word_substitute
from brian2.memory.dynamicarray import DynamicArray, DynamicArray1D
from brian2.codegen.languages.java_lang import java_data_type
from brian2.codegen.codeobject import CodeObjectUpdater

from .codeobject import AndroidCodeObject

__all__ = ['build']

def freeze(code, ns):
    # this is a bit of a hack, it should be passed to the template somehow
    for k, v in ns.items():
        if isinstance(v, (int, float)):
            code = word_substitute(code, {k: repr(v)})
    return code


class AndroidDevice(Device):
    '''
    '''
    def __init__(self):
        self.arrays = {}
        self.dynamic_arrays = {}
        self.code_objects = {}

    def array(self, owner, name, size, unit, dtype=None):
        if dtype is None:
            dtype = brian_prefs['core.default_scalar_dtype']
        arr = numpy.zeros(size, dtype=dtype)
        self.arrays['_array_%s_%s' % (owner.name, name)] = arr
        return arr

    def dynamic_array_1d(self, owner, name, size, unit, dtype):
        if dtype is None:
            dtype = brian_prefs['core.default_scalar_dtype']
        arr = DynamicArray1D(size, dtype=dtype)
        self.dynamic_arrays['_dynamic_array_%s_%s' % (owner.name, name)] = arr
        return arr

    def dynamic_array(self):
        raise NotImplentedError

    def code_object_class(self, codeobj_class=None):
        if codeobj_class is not None:
            raise ValueError("Cannot specify codeobj_class for Android device.")
        return AndroidCodeObject

    def code_object(self, owner, name, abstract_code, namespace, variables, template_name,
                    indices, variable_indices, codeobj_class=None,
                    template_kwds=None):
        codeobj = super(AndroidDevice, self).code_object(owner, name, abstract_code, namespace, variables,
                                                               template_name, indices, variable_indices,
                                                               codeobj_class=codeobj_class,
                                                               template_kwds=template_kwds,
                                                               )
        self.code_objects[codeobj.name] = codeobj
        return codeobj

    def build(self, net):
        # Extract all the CodeObjects
        # Note that since we ran the Network object, these CodeObjects will be sorted into the right
        # running order, assuming that there is only one clock
        print "building"
        updaters = []
        for obj in net.objects:
            for updater in obj.updaters:
                updaters.append(updater)

        # Extract the arrays information
        vars = {}
        for obj in net.objects:
            if hasattr(obj, 'variables'):
                for k, v in obj.variables.iteritems():
                    vars[(obj, k)] = v

        #if not os.path.exists('output'):
        #    os.mkdir('output')

        # Write the arrays
        # TODO: array code
        #array_specs = [(k, java_data_type(v.dtype), len(v)) for k, v in self.arrays.iteritems()]
        #dynamic_array_specs = [(k, java_data_type(v.dtype)) for k, v in self.dynamic_arrays.iteritems()]
        #arr_tmp = AndroidCodeObject.templater.arrays(None, array_specs=array_specs,
        #                                                   dynamic_array_specs=dynamic_array_specs)
        #open('output/arrays.java', 'w').write(arr_tmp.java_file)

        # Generate data for non-constant values
        code_object_defs = defaultdict(list)
        for codeobj in self.code_objects.itervalues():
            for k, v in codeobj.variables.iteritems():
                if k=='t':
                    pass
                elif isinstance(v, Subexpression):
                    pass
                elif not v.scalar:
                    N = v.get_len()
                    code_object_defs[codeobj.name].append('const int _num%s = %s;' % (k, N))
                    if isinstance(v, DynamicArrayVariable):
                        java_type = java_data_type(v.dtype)
                        # Create an alias name for the underlying array
                        code = ('{java_type}* {arrayname} = '
                                '&(_dynamic{arrayname}[0]);').format(java_type=java_type,
                                                                      arrayname=v.arrayname)
                        code_object_defs[codeobj.name].append(code)

        # Generate the updaters
        run_lines = []
        for updater in updaters:
            cls = updater.__class__
            if cls is CodeObjectUpdater:
                codeobj = updater.owner
                ns = codeobj.namespace
                # TODO: fix these freeze/CONSTANTS hacks somehow - they work but not elegant.
                print "codeobject: "+codeobj._name
                print "template attribs: ", codeobj.code.__dict__.keys()
                code_rs = freeze(codeobj.code.rs_file, ns)
                code_rs = code_rs.replace('%CONSTANTS%', '\n'.join(code_object_defs[codeobj.name]))

                code_java = freeze(codeobj.code.java_file, ns)

                print "name: "+codeobj.name
                print "rs code  : "+code_rs

                print "java code: "+code_java

                #open('output/'+codeobj.name+'.cpp', 'w').write(code)
                #open('output/'+codeobj.name+'.h', 'w').write(codeobj.code.h_file)

                #run_lines.append('_run_%s(t);' % codeobj.name)
            else:
                raise NotImplementedError("Android device has not implemented "+cls.__name__)

        # The code_objects are passed in the right order to run them because they were
        # sorted by the Network object. To support multiple clocks we'll need to be
        # smarter about that.
        # TODO: Use "main" template for dt, duration, and other global values
        #main_tmp = AndroidCodeObject.templater.main(None,
        #                                                  run_lines=run_lines,
        #                                                  code_objects=self.code_objects.values(),
        #                                                  num_steps=1000,
        #                                                  dt=float(defaultclock.dt),
        #                                                  )
        #open('output/main.java', 'w').write(main_tmp)

        # TODO: Print code to final templates
        # Copy the brianlibdirectory
        #brianlib_dir = os.path.join(os.path.split(inspect.getsourcefile(AndroidCodeObject))[0],
        #                            'brianlib')
        #copy_directory(brianlib_dir, 'output/brianlib')


android_device = AndroidDevice()

all_devices['android'] = android_device

def build(net):
    android_device.build(net)

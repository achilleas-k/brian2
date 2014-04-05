'''
Module implementing the Android "standalone" device
'''
import numpy
import os
import shutil
import subprocess
import inspect
from collections import defaultdict

from brian2.core.clocks import defaultclock
from brian2.core.network import Network
from brian2.devices.device import Device, all_devices
from brian2.core.variables import *
from brian2.synapses.synapses import Synapses
from brian2.utils.filetools import copy_directory, ensure_directory, in_directory
from brian2.utils.stringtools import word_substitute
#from brian2.codegen.generators.cpp_generator import c_data_type
from brian2.units.fundamentalunits import Quantity, have_same_dimensions
from brian2.units import second
from brian2.utils.logger import get_logger

from .codeobject import AndroidCodeObject

__all__ = []

logger = get_logger(__name__)


def freeze(code, ns):
    # this is a bit of a hack, it should be passed to the template somehow
    for k, v in ns.items():
        if isinstance(v, (int, float)):  # for the namespace provided for functions
            code = word_substitute(code, {k: str(v)})  # repr(v)???
        elif (isinstance(v, Variable) and not isinstance(v, AttributeVariable) and
              v.scalar and v.constant and v.read_only):
            code = word_substitute(code, {k: repr(v.get_value())})
    return code


class AndroidWriter(object):
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.source_files = []
        self.header_files = []

    def write(self, filename, contents):
        logger.debug('Writing file %s:\n%s' % (filename, contents))
        if filename.lower().endswith('.java'):
            self.java_files.append(filename)
        elif filename.lower().endswith('.rs'):
            self.renderscript_files.append(filename)
        fullfilename = os.path.join(self.project_dir, filename)
        if os.path.exists(fullfilename):
            if open(fullfilename, 'r').read() == contents:
                return
        open(fullfilename, 'w').write(contents)


def invert_dict(x):
    return dict((v, k) for k, v in x.iteritems())


class AndroidDevice(Device):
    '''
    The `Device` used for Android (BrianDroid) standalone simulations.
    '''
    def __init__(self):
        super(AndroidDevice, self).__init__()
        #: Dictionary mapping `ArrayVariable` objects to their globally
        #: unique name
        self.arrays = {}
        #: List of all dynamic arrays
        #: Dictionary mapping `DynamicArrayVariable` objects with 1 dimension to
        #: their globally unique name
        self.dynamic_arrays = {}
        #: Dictionary mapping `DynamicArrayVariable` objects with 2 dimensions
        #: to their globally unique name
        self.dynamic_arrays_2d = {}
        #: List of all arrays to be filled with zeros
        self.zero_arrays = []
        #: List of all arrays to be filled with numbers (tuple with
        #: `ArrayVariable` object and start value)
        self.arange_arrays = []

        #: Dict of all static saved arrays
        self.static_arrays = {}

        self.code_objects = {}
        self.main_queue = []

        self.synapses = []

        self.clocks = set([])

    def reinit(self):
        self.__init__()

    def insert_device_code(self, slot, code):
        '''
        Insert code directly into Simulation.java
        '''
        if slot=='main':
            self.main_queue.append(('insert_code', code))
        else:
            logger.warn("Ignoring device code, unknown slot: %s, code: %s" % (slot, code))

    def static_array(self, name, arr):
        assert len(arr), 'length for %s: %d' % (name, len(arr))
        name = '_static_array_' + name
        basename = name
        i = 0
        while name in self.static_arrays:
            i += 1
            name = basename+'_'+str(i)
        self.static_arrays[name] = arr.copy()
        return name

    def get_array_name(self, var, access_data=True):
        '''
        Return a globally unique name for `var`

        Parameters
        ----------
        access_data : bool, optional
            For `DynamicArrayVariable` objects, specifying `True` here means the
            name for the underlying data is returned. If specifying `False`,
            the name of the object itself is returned (e.g., to allow resizing).
        '''
        if isinstance(var, DynamicArrayVariable):
            if access_data:
                return self.arrays[var]
            elif var.dimenions == 1:
                return self.dynamic_arrays_2d[var]
        elif isinstance(var, ArrayVariable):
            return self.arrays[var]
        else:
            raise TypeError(('Do not have a name for variable of type '
                            '%s') % type(var))

    def add_array(self, var):
        # Note that a dynamic array variable is added to both the arrays and
        # the _dynamic_array dictionary
        if isinstance(var, DynamicArrayVariable):
            name = '_dynamic_array_%s_%s' % (var.owner.name, var.name)
            if var.dimensions == 1:
                self.dynamic_arrays[var] = name
            elif var.dimensions == 2:
                self.dynamic_arrays_2d[var] = name
            else:
                raise AssertionError(('Did not expect a dynamic array with %d'
                                        'dimensions') % var.dimensions)

            name = '_array_%s_%s' % (var.owner.name, var.name)
            self.arrays[var] = name

    def init_with_zeros(self, var):
        self.zero_arrays.append(var)

    def init_with_arange(self, var, start):
        self.arange_arrays.append((var, start))

    def fill_with_array(self, var, arr):
        arr = numpy.asarray(arr)
        if arr.shape == ():
            arr = numpy.repeat(arr, var.size)
        array_name = self.get_array_name(var, access_data=False)
        static_array_name = self.static_array(array_name, arr)
        self.main_queue.append(('set_by_array', (array_name,
                                                 static_array_name)))

    def group_set_with_index_array(self, group, variable_name, variable, item,
                                   value, check_units):
        if isinstance(item, slice) and item == slice(None):
            item = 'True'
        value = Quantity(value)

        if value.size == 1 and item == 'True':  # set the whole array to a scalar value
            if have_same_dimensions(value, 1):
                # Avoid a representation as "Quantity(...)" or "array(...)"
                value = float(value)
            group.set_with_expression_conditional(variable_name, variable,
                                                  cond=item,
                                                  code=repr(value),
                                                  check_units=check_units)
        # Simple case where we don't have to do any indexing
        elif item == 'True' and group.variable.indices(variable_name) == '_idx':
            self.fill_with_array(variable, value)
        else:
            # We have to calculate indices. This will not work for synaptic
            # variables
            try:
                indices = group.calc_indices(item)
            except NotImplementedError:
                raise NotImplementedError(('Cannot set variable "%s" this way in '
                                            'standalone, try using string '
                                            'expressions.') % variable_name)
            arrayname = self.get_array_name(variable, access_data=False)
            staticarrayname_index = self.static_array('_index_'+arrayname,
                                                      indices)
            staticarrayname_value = self.static_array('_value_'+arrayname,
                                                      value)
            self.main_queue.append(('set_array_by_array', (arrayname,
                                                           staticarrayname_index,
                                                           staticarrayname_value)))

    def group_get_with_index_array(self, group, variable_name, variable, item):
        raise NotImplementedError('Cannot retrieve the values of state '
                                  'variables in standalone code.')

    def group_get_with_expression(self, group, variable_name, variable, code,
                                  level=0, run_namespace=None):
        raise NotImplementedError('Cannot retrieve the values of state '
                                  'variables in standalone code.')

    def code_object_class(self, codeobj_class=None):
        if codeobj_class is not None:
            raise ValueError("Cannot specify codeobj_class for Android device")
        return AndroidCodeObject

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

    def code_object(self, owner, name, abstract_code, variables, template_name,
                    variable_indices, codeobj_class=None, template_kwds=None,
                    override_conditional_write=None):
        codeobj = super(AndroidDevice, self).code_object(
            owner, name, abstract_code, variables, template_name,
            variable_indices,
            codeobj_class=codeobj_class,
            template_kwds=template_kwds,
            override_conditional_write=override_conditional_write
        )
        self.code_objects[codeobj.name] = codeobj
        return codeobj

    def build(self, project_dir='output', compile_project=True, run_project=False, debug=True,
              with_output=True, native=True,
              additional_source_files=None, additional_header_files=None,
              main_includes=None, run_includes=None,  # these are probably useless
              run_args=None,
              ):
        # Extract all the CodeObjects
        # Note that since we ran the Network object, these CodeObjects will be sorted into the right
        # running order, assuming that there is only one clock
        # TODO: Reorganise/simplify the template system
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


        if not os.path.exists('output'):
            os.mkdir('output')

        # Arrays code
        array_specs = [(k, java_data_type(v.dtype), len(v)) for k, v in self.arrays.iteritems()]
        arr_tmp = AndroidCodeObject.templater.arrays(None, array_specs=array_specs)
        arrays_java = arr_tmp.java_code
        arrays_rs = arr_tmp.rs_code


        code_object_defs = defaultdict(list)
        idx_init = ''
        for codeobj in self.code_objects.itervalues():
            # Indexer initialisation code
            if hasattr(codeobj.owner, "N"):
                idx_tmp = AndroidCodeObject.templater.idx_initialisations(
                    None, codeobj_name=codeobj.name,
                    N=codeobj.owner.N)
                idx_init += idx_tmp.java_code
            for k, v in codeobj.variables.iteritems():
                if k=='t':
                    pass
                elif isinstance(v, Subexpression):
                    pass
                elif not v.scalar:
                    N = v.get_len()
                    code_object_defs[codeobj.name].append('const int _num%s = %s;' % (k, N))
                    if isinstance(v, DynamicArrayVariable):
                        pass

        # Generate the updaters
        update_code_rs = ""
        update_code_java = ""
        monitor_listing = ""
        for updater in updaters:
            cls = updater.__class__
            if cls is CodeObjectUpdater:
                codeobj = updater.owner
                ns = codeobj.namespace
                # TODO: CONSTANTS
                if hasattr(codeobj.code, "rs_code"):
                    update_code_rs += freeze(codeobj.code.rs_code, ns)
                    #code_rs = code_rs.replace('%CONSTANTS%', '\n'.join(code_object_defs[codeobj.name]))
                if hasattr(codeobj.code, "java_code"):
                    update_code_java += freeze(codeobj.code.java_code, ns)
                if hasattr(codeobj.code, "monitor_declaration"):
                    arrays_java += codeobj.code.monitor_declaration
                if hasattr(codeobj.code, "monitor_listing"):
                    monitor_listing += codeobj.code.monitor_listing
            else:
                raise NotImplementedError("Android device has not implemented "+cls.__name__)

        simulation_file_code = AndroidCodeObject.templater.Simulation(None,
                                                                      arrays=arrays_java,
                                                                      kernel_calls=update_code_java,
                                                                      duration=1,  # NOTE: Duration
                                                                      dt=float(defaultclock.dt),
                                                                      idx_initialisations=idx_init,
                                                                      monitor_listing=monitor_listing,
                                                                      )
        renderscript_file_code = AndroidCodeObject.templater.renderscript(None,
                                                                          arrays=arrays_rs,
                                                                          #constants=constants,
                                                                          updaters=update_code_rs,
                                                                          dt=float(defaultclock.dt)
        )
        open('output/Simulation.java', 'w').write(simulation_file_code)
        open('output/renderscript.rs', 'w').write(renderscript_file_code)
        print("Code generation complete. Generated code can be found in ``output`` directory.")

    def network_run(self, net, duration, report=None, report_period=60*second,
                    namespace=None, level=0):

        # We have to use +2 for the level argument here, since this function is
        # called through the device_override mechanism
        net.before_run(namespace, level=level+2)

        self.clocks.update(net._clocks)

        # TODO: from cpp_standalone/device.py - "remove this horrible hack"
        for clock in self.clocks:
            if clock.name == 'clock':
                clock._name = '_clock'

        # Extract all the CodeObjects
        # Note that since we ran the Network object, these CodeObjects will be sorted into the right
        # running order, assuming that there is only one clock
        code_objects = []
        for obj in net.objects:
            for codeobj in obj._code_objects:
                code_objects.append((obj.clock, codeobj))

        # Generate the updaters
        run_lines = ['{net.name}.clear();'.format(net=net)]
        for clock, codeobj in code_objects:
            run_lines.append('{net.name}.add({clock.name}, _run_{codeobj.name});'.format(clock=clock, net=net,
                                                                                         codeobj-codeobj))
        run_lines.append('{net.name}.run({duration});'.format(net=net, duration=float(duration)))
        self.main_queue.append(('run_network', (net, run_lines)))

    def run_function(self, name, include_in_parent=True):
        '''
        Context manager to divert code into a function

        Code that happens within the scope of this context manager will go into the named function.

        Parameters
        ----------
        name : str
            The name of the function to divert code into.
        include_in_parent : bool
            Whether or not to include a call to the newly defined function in the parent context.
        '''
        return RunFunctionContext(name, include_in_parent)

class RunFunctionContext(object):
    def __init__(self, name, include_in_parent):
        self.name = name
        self.include_in_parent = include_in_parent
    def __enter__(self):
        android_standalone_device.main_queue.append(('start_run_func', (self.name, self.include_in_parent)))
    def __exit__(self):
        android_standalone_device.main_queue.append(('end_run_func', (self.name, self.include_in_parent)))


android_device = AndroidDevice()

all_devices['android'] = android_device



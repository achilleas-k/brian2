import numpy
import brian2
from brian2.devices.cpp.standalone_cpp import CPPMethodHandler

class NeuronGroupHandler(CPPMethodHandler):
    handle_class = brian2.NeuronGroup
    method_names = {'__init__':True,
                    'set_state_':True,
                    }
    
    def set_state_(self, proc):
        var, val = proc.args
        if isinstance(val, (str, numpy.ndarray)):
            raise ValueError("Can only handle scalar values for now.")
        return '{{objname}}.set_state("{{args[0]}}", {{args[1]}});'
    
    init = 'C_{{objname}} {{objname}}("{{obj.when}}", {{obj.order}}, {{obj.clock.name}}, {{obj._num_neurons}});'

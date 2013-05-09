import numpy
import brian2
from brian2.devices.cpp.standalone_cpp import CPPMethodHandler
from brian2.groups.group import GroupCodeRunner
from brian2.groups.neurongroup import Thresholder, Resetter

# We use this temporary hack to get the thresholder code in a form we can
# use - this will change when we refactor CPPLanguage to use Jinja templates
class FakeThresholder(Thresholder):
    def __init__(self, group):
        GroupCodeRunner.__init__(self, group,
                                 lambda:{'hashdefines':'%HASHDEFINES%',
                                         'pointers':'%POINTERS%',
                                         'code':'%CODE%'},
                                 when=(group.clock, 'thresholds'),
                                 name=group.name + '_thresholder_fake')
class FakeResetter(Resetter):
    def __init__(self, group):
        GroupCodeRunner.__init__(self, group,
                                 lambda:{'hashdefines':'%HASHDEFINES%',
                                         'pointers':'%POINTERS%',
                                         'code':'%CODE%'},
                                 when=(group.clock, 'resets'),
                                 name=group.name + '_resetter_fake',
                                 iterate_all=False)


class NeuronGroupHandler(CPPMethodHandler):
    handle_class = brian2.NeuronGroup
    method_names = {'__init__':True,
                    'set_state_':True,
                    }
    
    def set_state_(self, proc):
        var, val = proc.args
        if (isinstance(val, numpy.ndarray) and val.shape!=()):
            raise ValueError("Can only handle scalar values for now. "+str(proc))
        return '{{objname}}.set_state("{{args[0]}}", {{args[1]|float}});'

    def init(self, proc):
        # Create thresholder C++ code
        G = proc.obj
        thr = FakeThresholder(G)
        proc.thresholder_code = thr.codeobj.code
        # Create resetter C++ code
        res = FakeResetter(G)
        proc.resetter_code = res.codeobj.code
        # Return code to insert into main.cpp
        return 'C_{{objname}} {{objname}}("{{obj.when}}", {{obj.order}}, {{obj.clock.name}}, {{obj._num_neurons}});'

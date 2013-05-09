import numpy
import brian2
from brian2.devices.cpp.standalone_cpp import CPPMethodHandler

class NetworkHandler(CPPMethodHandler):
    handle_class = brian2.Network
    method_names = {'__init__': True,
                    'run': False,
                    }

    init = '''
    Network {{objname}};
    {% for o in args %}
    {{objname}}.add({{o.name}});
    {% endfor %}
    '''
    
    run = '{{objname}}.run({{args[0]|float}});'

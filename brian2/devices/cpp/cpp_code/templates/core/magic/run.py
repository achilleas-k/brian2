import numpy
import brian2
from brian2.devices.cpp.standalone_cpp import CPPFunctionHandler

class RunHandler(CPPFunctionHandler):
    handle_function = brian2.run
    runit = False
    call = '{{call_representation}}'    


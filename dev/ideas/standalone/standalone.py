from brian2 import *
from brian2.devices.cpp import *
from brian2.devices.cpp.standalone_cpp import implementation

eqs = '''
dV/dt = -V/(10*ms) : 1
'''

G = NeuronGroup(10, eqs)
G.V = 1

Network(G)

run(100*ms)

build()

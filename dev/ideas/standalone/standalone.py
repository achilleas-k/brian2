from brian2 import *
from brian2.devices.cpp import *

eqs = '''
dV/dt = -V/(10*ms) : 1
'''

G = NeuronGroup(10, eqs)

Network(G)

run(100*ms)

build()

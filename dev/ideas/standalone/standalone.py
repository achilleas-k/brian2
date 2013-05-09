from brian2 import *
from brian2.devices.cpp import *
import os
from numpy import loadtxt
from pylab import plot, show

eqs = '''
dV/dt = (2-V)/(10*ms) : 1
'''

G = NeuronGroup(10, eqs, threshold='V>1', reset='V = 0')
G.V = 1

net = Network(G)

net.run(100*ms)

#print '%g'%G.V[0]

insert_code('''
    cout << "Next two lines should be the same:\\n0.346082\\n";
    cout << neurongroup_0.arrays["V"][0] << endl;
''')

build(run=True)

i, t = loadtxt('output/neurongroup_0.spikes.txt').T
plot(t, i, '.k')
show()

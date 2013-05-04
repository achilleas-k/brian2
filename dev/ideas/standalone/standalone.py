from brian2 import *
from brian2.devices.cpp import *

eqs = '''
dV/dt = -V/(10*ms) : 1
'''

G = NeuronGroup(10, eqs)
G.V = 1

net = Network(G)

run(100*ms)

insert_code('''
    for(scalar t=0.0; t<100*ms; t+=defaultclock.dt)
    {
        neurongroup_0.state_update();
    }
    cout << neurongroup_0.arrays["V"][0] << endl;

    // DEBUG STUFF
    Network net = Network();
    net.add(neurongroup_0);
    cout << net.objects.size() << endl;

''')

build()

from brian2 import *

ondevice = True

if ondevice:
    from brian2.devices.cpp import *

import os
import time
from pylab import plot, show, linspace, loadtxt, array, bincount

start = time.time()

if ondevice:
    insert_code('''
    clock_t start = clock();
    ''')

N = 1000
eqs = '''
dv/dt=(v0-v)/(10*ms) : volt
v0 : volt
'''
group = NeuronGroup(N, eqs, threshold='v>10 * mV',
                    reset='v = 0 * mV')
#group.refractory = 5 * ms # not supported yet
group.v = 0 * mV
v0 = linspace(0 * mV, 20 * mV, N)
if not ondevice:
    group.v0 = v0
else:
    insert_code('''
    scalar *v0 = neurongroup_0.arrays["v0"];
    for(int i=0; i<neurongroup_0._num_neurons; i++)
    {
      v0[i] = 20*mV*(scalar)i/(neurongroup_0._num_neurons-1);
    }
    ''')

duration = 5 * second
net = Network(group)

if not ondevice:
    monitor = SpikeMonitor(group)
    net.add(monitor)

start_sim = time.time()
if ondevice:
    insert_code('''
    clock_t start_sim = clock();
    ''')

net.run(duration)

end_sim = time.time()
if ondevice:
    insert_code('''
    clock_t end_sim = clock();
    ''')

if ondevice:
    insert_code('''
    cout << "Preparation time: " << double( start_sim-start ) / (double)CLOCKS_PER_SEC << endl;
    cout << "Run time: " << double( end_sim-start_sim ) / (double)CLOCKS_PER_SEC << endl;
    ''')
else:
    print 'Preparation time:', start_sim-start
    print 'Run time:', end_sim-start_sim

if ondevice:
    # We have to hack this for the moment
    net.pre_run(('implicit-run-namespace', globals()))
    build(run=True)

if ondevice:
    i, t = loadtxt('output/neurongroup_0.spikes.txt').T
    i = array(i, dtype=int)
else:
    i, t = monitor.it

count = bincount(i, minlength=N)

plot(v0, count/duration)
show()

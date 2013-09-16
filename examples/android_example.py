from numpy import *
from brian2 import *
from brian2.devices.android_standalone import *

set_device('android')
##### Define the model
tau_a = 10*ms
tau_b = 20*ms
eqs_a = '''
dV/dt = -V/tau_a : volt (unless-refractory)
'''
eqs_b = '''
dV/dt = -V/tau_b : volt (unless-refractory)
'''
threshold = 'V>-50*mV'
reset = 'V=-60*mV'
refractory = 5*ms
N = 1000

G = NeuronGroup(N, eqs_a, reset=reset, threshold=threshold, refractory=refractory, name='gp')
G2 = NeuronGroup(10, eqs_b, reset=reset, threshold=threshold, refractory=refractory, name='gp2')
G.V = -1*mV
SM = SpikeMonitor(G)
net = Network(G, G2, SM)
#net.generate_code()
net.run(0*second)
build(net)


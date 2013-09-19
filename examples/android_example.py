from numpy import *
from brian2 import *
from brian2.devices.android_standalone import *

set_device('android')
##### Define the model
tau_a = 10*ms
tau_b = 20*ms
V0 = -49*mV
eqs_a = '''
dV/dt = (V0-V)/tau_a : volt (unless-refractory)
'''
eqs_b = '''
dV/dt = (V0-V)/tau_b : volt (unless-refractory)
'''
threshold = 'V>-50*mV'
reset = 'V=-60*mV'
refractory = 5*ms
N = 1000

G1 = NeuronGroup(N, eqs_a, reset=reset, threshold=threshold, refractory=refractory, name='gp1')
G2 = NeuronGroup(10, eqs_b, reset=reset, threshold=threshold, refractory=refractory, name='gp2')
#G.V = '-1*mV'
SM1 = SpikeMonitor(G1)
SM2 = SpikeMonitor(G2)
#VM = StateMonitor(G, 'V', record=True)
net = Network(G1, G2, SM1, SM2)
#net.generate_code()
net.run(0*second)
build(net)


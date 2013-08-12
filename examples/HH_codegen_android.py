'''
TODO: modify this so to just generate snippets
'''
from numpy import *
from brian2 import *
from brian2.utils.stringtools import *
from brian2.codegen.languages.java_lang import *

##### Define the model
tau = 10*ms

# Parameters
area = 20000 * umetre ** 2
Cm = (1 * ufarad * cm ** -2) * area
gl = (5e-5 * siemens * cm ** -2) * area
El = -65 * mV
EK = -90 * mV
ENa = 50 * mV
g_na = (100 * msiemens * cm ** -2) * area
g_kd = (30 * msiemens * cm ** -2) * area
VT = -63 * mV



eqs = Equations('''
dv/dt = (gl*(El-v) - g_na*(m*m*m)*h*(v-ENa) - g_kd*(n*n*n*n)*(v-EK) + I)/Cm : volt
dm/dt = 0.32*(mV**-1)*(13.*mV-v+VT)/
    (exp((13.*mV-v+VT)/(4.*mV))-1.)/ms*(1-m)-0.28*(mV**-1)*(v-VT-40.*mV)/
    (exp((v-VT-40.*mV)/(5.*mV))-1.)/ms*m : 1
dn/dt = 0.032*(mV**-1)*(15.*mV-v+VT)/
    (exp((15.*mV-v+VT)/(5.*mV))-1.)/ms*(1.-n)-.5*exp((10.*mV-v+VT)/(40.*mV))/ms*n : 1
dh/dt = 0.128*exp((17.*mV-v+VT)/(18.*mV))/ms*(1.-h)-4./(1+exp((40.*mV-v+VT)/(5.*mV)))/ms*h : 1
I : amp
''')

threshold = 'not_refractory and (v>-40*mV)'
refractory = 'v > -40*mV'
groupname = 'gp'
N = 100

##### Generate android code

# Use a NeuronGroup to fake the whole process
G = NeuronGroup(N, eqs, threshold=threshold,
                refractory=refractory, name=groupname,
                codeobj_class=JavaCodeObject,
                )
# Run the network for 0 seconds to generate the code
net = Network(G)
net.run(0*second)
# Extract the necessary information
ns = G.state_updater.codeobj.namespace
code = deindent(G.state_updater.codeobj.code.main)
arrays = []
# Freeze all constants
for k, v in ns.items():
    if isinstance(v, float):
        code = ('final double %s = %s;\n' % (k, repr(v)))+code
    elif isinstance(v, int):
        code = ('final int %s = %s;\n' % (k, repr(v)))+code
    elif isinstance(v, ndarray):
        if k.startswith('_array'):
            dtype_spec = java_data_type(v.dtype)
            arrays.append((k, dtype_spec, N))


print '//*********** PUBLIC VARS **********'
for varname, dtype_spec, N in arrays:
    print '%s[] %s;' % (dtype_spec, varname)

print '//*********** SETUP METHOD *********'
print 'public void setup() {'
for varname, dtype_spec, N in arrays:
    print '%s = new %s [%s];' % (varname, dtype_spec, N)
print '}'

print '//*********** MAIN LOOP *************'
print 'public void run() {'
print 'for (t=0; t<_duration; t+=dt) {'
print code
print '}}'


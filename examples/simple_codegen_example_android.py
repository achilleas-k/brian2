'''
TODO: modify this so to just generate snippets
'''
from numpy import *
from brian2 import *
from brian2.utils.stringtools import *
from brian2.codegen.languages.java_lang import *

##### Define the model
tau = 10*ms
eqs = '''
dV/dt = -V/tau : volt (unless-refractory)
'''
threshold = 'V>-50*mV'
reset = 'V=-60*mV'
refractory = 5*ms
groupname = 'gp'
N = 1000

##### Generate C++ code

# Use a NeuronGroup to fake the whole process
G = NeuronGroup(N, eqs, reset=reset, threshold=threshold,
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
print code
print '}'


#include<math.h>
#include "{{objname}}.h"

#define dt ({{obj.clock.dt|float}})

CLASSNAME::CLASSNAME(string When, scalar Order, Clock &c, int N) :
		NeuronGroup(When, Order, c, N)
{
	allocate_memory();
}

CLASSNAME::~CLASSNAME()
{
	deallocate_memory();
}

void CLASSNAME::allocate_memory()
{
	// TODO: check for memory allocation failures and raise exception
	{% for var in obj.arrays.keys() %}
	_array_{{var}} = new scalar [_num_neurons];
	arrays[{{'"'+var+'"'}}] = _array_{{var}};
	{% endfor %}
}

void CLASSNAME::deallocate_memory()
{
	{% for var in obj.arrays.keys() %}
	if(_array_{{var}})
	{
		delete [] _array_{{var}};
		_array_{{var}} = 0;
	}
	{% endfor %}
	arrays.clear();
}

void CLASSNAME::state_update()
{
	{{obj.state_updater.codeobj.code['%MAIN%']}}
}

void CLASSNAME::thresholder()
{
	spikes.clear();
	{{thresholder_code.hashdefines}}
	{{thresholder_code.pointers}}
    for(int _neuron_idx=0; _neuron_idx<_num_neurons; _neuron_idx++)
    {
    	{{thresholder_code.code}}
    	if(_cond) {
    		spikes.push_back(_neuron_idx);
    	}
    }
}

void CLASSNAME::resetter()
{
	{{resetter_code.hashdefines}}
	{{resetter_code.pointers}}
	for(vector<int>::iterator _spike_iterator=spikes.begin(); _spike_iterator!=spikes.end(); _spike_iterator++)
	{
		int _neuron_idx = *_spike_iterator;
    	{{resetter_code.code}}
    }
}

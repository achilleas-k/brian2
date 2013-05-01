#include "{{name}}.h"

const scalar dt = {{dt}};

void CLASSNAME::_init()
{
	NeuronGroup::_init();
	_num_neurons = {{num_neurons}};
}

void CLASSNAME::allocate_memory()
{
	// TODO: check for memory allocation failures and raise exception
	{% for var in variables %}
	_array_{{var}} = new scalar [_num_neurons];
	{% endfor %}
}

void CLASSNAME::deallocate_memory()
{
	{% for var in variables %}
	if(_array_{{var}})
	{
		delete [] _array_{{var}};
		_array_{{var}} = 0;
	}
	{% endfor %}
}

void CLASSNAME::state_update()
{
	{{state_update_code}}
}

CLASSNAME OBJNAME;

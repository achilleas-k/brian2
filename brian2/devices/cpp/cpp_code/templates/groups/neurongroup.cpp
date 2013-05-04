#include "{{name}}.h"

#define dt ({{dt}})

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
	{% for var in variables %}
	_array_{{var}} = new scalar [_num_neurons];
	arrays[{{'"'+var+'"'}}] = _array_{{var}};
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
	arrays.clear();
}

void CLASSNAME::state_update()
{
	{{state_update_code}}
}

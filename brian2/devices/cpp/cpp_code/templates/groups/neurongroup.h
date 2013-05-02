// Brian library includes
#include "brianlib/groups.h"
#include "brianlib/briantypes.h"
#include "brianlib/units.h"
#include "brianlib/core.h"

#define CLASSNAME C_{{name}}
#define OBJNAME {{name}}

class CLASSNAME : public NeuronGroup
{
public:
	int _num_neurons;
	// Array memory
	{% for var in variables %}
	scalar *_array_{{var}};
	{% endfor %}
	
	// Methods
	void _init();
	void allocate_memory();
	void deallocate_memory();
	void state_update();
};

extern CLASSNAME OBJNAME;

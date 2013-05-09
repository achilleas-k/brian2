#ifndef _BRIAN_TEMPLATES_{{objname}}_H
#define _BRIAN_TEMPLATES_{{objname}}_H

// Brian library includes
#include "brianlib/groups.h"
#include "brianlib/briantypes.h"
#include "brianlib/units.h"
#include "brianlib/core.h"

#define CLASSNAME C_{{objname}}
#define OBJNAME {{objname}}

class CLASSNAME : public NeuronGroup
{
public:
	// Array memory
	{% for var in obj.arrays.keys() %}
	scalar *_array_{{var}};
	{% endfor %}
	// Constructor
	CLASSNAME(string When, scalar Order, Clock &c, int N);
	~CLASSNAME();
	// Methods
	void allocate_memory();
	void deallocate_memory();
	virtual void state_update();
};

#endif

// Core C/C++ includes
#include<math.h>

// Brian library includes
#include "brianlib/units.h"
#include "brianlib/magic.h"

// Brian object includes
{% for obj in objects %}
#include "{{obj.name}}.h"
{% endfor %}


int main(int argc, char **argv)
{
	// Main procedures
	{% for procline in procedure_lines %}
	{{procline}};
	{% endfor %}
}

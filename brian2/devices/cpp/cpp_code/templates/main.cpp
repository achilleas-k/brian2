#include<iostream>

using namespace std;

// Brian library includes
#include "brianlib/units.h"
#include "brianlib/core.h"
#include "brianlib/groups.h"

// Brian extra includes
{% for header in headers %}
#include "{{header}}"
{% endfor %}

int main(int argc, char **argv)
{
	// Declare global objects which are not explicitly declared in script
	Clock defaultclock({{defaultclock.dt_}});

	// Main procedures
	{% for procline in procedure_lines %}
	{{procline}};
	{% endfor %}	
}

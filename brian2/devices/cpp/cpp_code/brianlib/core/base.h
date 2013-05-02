#ifndef _BRIAN_BRIANLIB_CORE_BASE_H
#define _BRIAN_BRIANLIB_CORE_BASE_H

#include <string>

using namespace std;

#include "clocks.h"

class BrianObject
{
public:
	string when;
	scalar order;
	Clock &clock;
	// Constructor
	BrianObject(string When, scalar Order, Clock &c) :
		when(When), order(Order), clock(c) {};
	// Methods
	void prepare() {};
	void reinit() {};
	// TODO: active, contained_objects
};

#endif

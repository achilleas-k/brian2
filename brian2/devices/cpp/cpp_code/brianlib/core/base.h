#ifndef _BRIANOBJECT_H
#define _BRIANOBJECT_H

//TODO: this raises an error, why?
//#include<string>

//using namespace std;

#include "clocks.h"

class BrianObject
{
public:
	//std::string when;
	scalar order;
	Clock &clock;
	// Constructor
	BrianObject(/*std::string When,*/ scalar Order, Clock &c) :
		/*when(When),*/ order(Order), clock(c) {};
	// Methods
	void prepare() {};
	void reinit() {};
	// TODO: active, contained_objects
};

#endif

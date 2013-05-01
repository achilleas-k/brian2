#ifndef _BRIANOBJECT_H
#define _BRIANOBJECT_H

#include "clocks.h"

class BrianObject
{
public:
	Clock clock;
	// Constructor
	BrianObject(int when, scalar order, Clock c);
};

#endif

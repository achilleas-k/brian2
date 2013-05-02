#ifndef _BRIAN_BRIANLIB_CORE_NETWORK_H
#define _BRIAN_BRIANLIB_CORE_NETWORK_H

#include "base.h"
#include<list>

using namespace std;

class Network
{
public:
	list<BrianObject*> objects;
	// Methods
	void add(BrianObject &obj);
};

#endif

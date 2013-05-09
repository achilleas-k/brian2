#ifndef _BRIAN_BRIANLIB_GROUPS_NEURONGROUP_H
#define _BRIAN_BRIANLIB_GROUPS_NEURONGROUP_H

#include<list>
#include<string>

using namespace std;

#include "brianlib/core/base.h"
#include "brianlib/core/spikesource.h"
#include "brianlib/briancpputil.h"

class NeuronGroup : public BrianObject, public SpikeSource
{
public:
	int _num_neurons;
	unordered_map<string, scalar*> arrays;
	// Constructors
	NeuronGroup(string When, scalar Order, Clock &c, int N);
	// Methods
	virtual void state_update() = 0;
	virtual void update();
	void set_state(string name, scalar value);
	virtual void thresholder() = 0;
	virtual void resetter() = 0;
};

#endif

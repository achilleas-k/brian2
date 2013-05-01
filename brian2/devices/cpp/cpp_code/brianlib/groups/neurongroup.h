#ifndef _NEURONGROUP_H
#define _NEURONGROUP_H

class NeuronGroup
{
public:
	void _init();
	~NeuronGroup();
	// Methods which should be overridden
	void state_update() {};
	void allocate_memory() {};
	void deallocate_memory() {};
};

#endif
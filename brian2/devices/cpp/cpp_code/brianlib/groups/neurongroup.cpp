#include "neurongroup.h"


NeuronGroup::NeuronGroup(string When, scalar Order, Clock &c) :
	BrianObject(When, Order, c)
{
	allocate_memory();
}

NeuronGroup::~NeuronGroup()
{
	deallocate_memory();
}

void NeuronGroup::update()
{
	state_update();
}
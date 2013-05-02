#include "neurongroup.h"

/*
NeuronGroup::NeuronGroup(string When, scalar Order, Clock &c) :
	BrianObject(When, Order, c)
{
}
*/

void NeuronGroup::_init()
{
	allocate_memory();
}

NeuronGroup::~NeuronGroup()
{
	deallocate_memory();
}

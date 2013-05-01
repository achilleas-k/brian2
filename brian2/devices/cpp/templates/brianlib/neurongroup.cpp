#include "neurongroup.h"

void NeuronGroup::_init()
{
	allocate_memory();
}

NeuronGroup::~NeuronGroup()
{
	deallocate_memory();
}

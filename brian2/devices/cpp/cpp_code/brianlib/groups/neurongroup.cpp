#include "neurongroup.h"


NeuronGroup::NeuronGroup(string When, scalar Order, Clock &c, int N) :
	BrianObject(When, Order, c)
{
	_num_neurons = N;
}

void NeuronGroup::update()
{
	state_update();
}

void NeuronGroup::set_state(string name, scalar value)
{
	scalar *arr = arrays[name];
	for(int i=0; i<_num_neurons; i++)
		arr[i] = value;
}

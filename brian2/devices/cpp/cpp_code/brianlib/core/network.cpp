#include "network.h"

void Network::add(BrianObject &obj)
{
	objects.push_back(&obj);
}

void Network::run(scalar duration)
{
	if(objects.size()==0) return;
	// HORRIBLE HACK, NEEDS TO DO THE SAME AS NETWORK! TODO: Fix this
	Clock &clock = (*(objects.begin()))->clock;
	scalar t_end = duration;
	clock.set_interval(0.0, t_end);
	while(clock.running())
	{
		for(list<BrianObject*>::iterator it=objects.begin(); it!=objects.end(); it++)
		{
			BrianObject *obj = *it;
			obj->update();
		}
		clock.tick();
	}
}

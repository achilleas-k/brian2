#ifndef _BRIAN_BRIANLIB_CORE_CLOCKS_H
#define _BRIAN_BRIANLIB_CORE_CLOCKS_H

#include "brianlib/briantypes.h"

#define clock_epsilon (1.0e-14)

class Clock
{
public:
	scalar dt; // The time step of the simulation as a float (in seconds)
	int i; // The time step of the simulation as an integer.
	int i_end; // The time step the simulation will end as an integer
	// Constructor
	Clock(scalar DT);
	// Methods
	void set_interval(scalar start, scalar end);
	// Inline methods
	inline void tick() { i += 1; };
	inline scalar t() { return i*dt; };
	inline scalar t_end() { return i_end*dt; };
	inline scalar set_t(scalar newt) { i = (int)(newt/dt); };
	inline scalar set_t_end(scalar newt_end) { i_end = (int)(newt_end/dt); };
	inline bool running() { return i<i_end; };
};

#endif

#include<math.h>
#include "clocks.h"

// rounds to nearest int for positive values
#define round(x) (int)((x)+0.5)
#define abs(x) ((x)>0?(x):(-(x)))

Clock::Clock(scalar DT)
{
	dt = DT;
	i = 0;
	i_end = 0;
}

/*
Set the start and end time of the simulation.

Sets the start and end value of the clock precisely if
possible (using epsilon) or rounding up if not. This assures that
multiple calls to `Network.run` will not re-run the same time step.
*/
void Clock::set_interval(scalar start, scalar end)
{
    int i_start = round(start/dt);
    scalar t_start = i_start*dt;
    if(t_start==start or abs(t_start-start)<=clock_epsilon*abs(t_start))
    {
        i = i_start;
    } else
    {
        i = (int)ceil(start/dt);
    }
    int i_end = round(end/dt);
    scalar t_end = i_end*dt;
    if(t_end==end or abs(t_end-end)<=clock_epsilon*abs(t_end))
    {
        this->i_end = i_end;
    } else
    {
        this->i_end = (int)ceil(end/dt);
    }
}

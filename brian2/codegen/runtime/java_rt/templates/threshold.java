////////////////////////////////////////////////////////////////////////////
//// MAIN CODE /////////////////////////////////////////////////////////////

{% macro main() %}
	// USE_SPECIFIERS { _num_neurons, not_refractory, lastspike, t }
	////// SUPPORT CODE ///////
	{% for line in support_code_lines %}
	// {{line}}
	{% endfor %}

	//// MAIN CODE ////////////
	ArrayList<Integer> _spikes_space = new ArrayList<Integer>();
        // TODO: use normal array so I can pass to renderscript and add an extra variable for the number of spikes
        // array size would be number of neurons
	for(int _neuron_idx=0; _neuron_idx<_num_neurons; _neuron_idx++)
	{
	    final int _vectorisation_idx = _neuron_idx;
		{% for line in code_lines %}
		{{line}}
		{% endfor %}
		if(_cond) {
                    _spikes_space.add(_neuron_idx);
                    not_refractory[_neuron_idx] = false;
                    lastspike[_neuron_idx] = t;
		}
	}
	return_val = _spikes_space.size();
{% endmacro %}

////////////////////////////////////////////////////////////////////////////
//// SUPPORT CODE //////////////////////////////////////////////////////////

{% macro support_code() %}
	{% for line in support_code_lines %}
	// {{line}}
	{% endfor %}
{% endmacro %}




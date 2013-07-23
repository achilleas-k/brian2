////////////////////////////////////////////////////////////////////////////
//// MAIN CODE /////////////////////////////////////////////////////////////

{% macro main() %}
	// USE_SPECIFIERS { _num_neurons }
	////// SUPPORT CODE ///////
	{% for line in support_code_lines %}
	// {{line}}
	{% endfor %}

	////// HANDLE DENORMALS ///
	//{% for line in denormals_code_lines %}
	//{{line}}
	//{% endfor %}

	////// HASH DEFINES ///////
	//{% for line in hashdefine_lines %}
	//{{line}}
	//{% endfor %}

	///// POINTERS ////////////
	//{% for line in pointers_lines %}
	//{{line}}
	//{% endfor %}

	//// MAIN CODE ////////////
	// Container for all the potential indices
        // Fixed size? Maybe change to regular array
        ArrayList<Integer> _elements = new ArrayList<Integer>();
	for(int _neuron_idx=0; _neuron_idx<_num_neurons; _neuron_idx++)
	{
	    const int _vectorisation_idx = _neuron_idx; // ???
		{% for line in code_lines %}
		{{line}}
		{% endfor %}
		if(_cond) {
                    _elements.add(_neuron_idx);

		}
	}
	return_val = _elements.size()
{% endmacro %}

////////////////////////////////////////////////////////////////////////////
//// SUPPORT CODE //////////////////////////////////////////////////////////

{% macro support_code() %}
	{% for line in support_code_lines %}
	// {{line}}
	{% endfor %}
{% endmacro %}

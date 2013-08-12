//// MAIN CODE /////////////////////////////////////////////////////////////

{% macro main() %}
	// USE_SPECIFIERS { _num_neurons }

    ////// SUPPORT CODE ///
	{% for line in support_code_lines %}
	//{{line}}
	{% endfor %}


	for(int _neuron_idx=0; _neuron_idx<_num_neurons; _neuron_idx++)
	{
	    final int _vectorisation_idx = _neuron_idx;
		{% for line in code_lines %}
		{{line}}
		{% endfor %}
	}
{% endmacro %}

////////////////////////////////////////////////////////////////////////////
//// SUPPORT CODE //////////////////////////////////////////////////////////

{% macro support_code() %}
	{% for line in support_code_lines %}
	{{line}}
	{% endfor %}
{% endmacro %}




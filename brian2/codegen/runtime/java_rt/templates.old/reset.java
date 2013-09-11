//// MAIN CODE /////////////////////////////////////////////////////////////

{% macro main() %}
	// USE_SPECIFIERS { _spikes }

	//// MAIN CODE ////////////
	for(int _index__spikes=0; _index__spikes<_num_spikes; _index__spikes++)
	{
		final int _neuron_idx = _spikes[_index__spikes];
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



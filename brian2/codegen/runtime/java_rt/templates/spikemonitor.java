{% macro rs_file() %}

{% endmacro %}

{% macro java_file() %}

    if (_num_spikes > 0)
    {
        // Copy the values across
        for(int _idx=0; _idx<_num_spikes; _idx++)
        {
            final int _neuron_idx = _spikes[_idx];
            {{codeobj_name}}_spikemonitor.append(new Spike(_idx, t));
            //_count[_neuron_idx]++;
        }
    }
{% endmacro %}


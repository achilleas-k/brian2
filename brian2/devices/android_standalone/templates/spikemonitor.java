{% macro main() %}

    // USE_SPECIFIERS { _t, _i, t, _spikes, _count }

    if (_num_spikes > 0)
    {
        // Copy the values across
        for(int _idx=0; _idx<_num_spikes; _idx++)
        {
            final int _neuron_idx = _spikes[_idx];
            _t_data.add(t);
            _i_data.add(_neuron_idx);
            _count[_neuron_idx]++;
        }
    }
{% endmacro %}

{% macro support_code() %}
{% endmacro %}



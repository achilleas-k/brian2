{% macro main() %}

    // USE_SPECIFIERS { _t, _rate, t, dt, _spikes }
    _t_data.add(t);
    _rate_data.add(1.0*_num_spikes / (float)dt / _num_source_neurons)

{% endmacro %}

{% macro support_code() %}
{% endmacro %}



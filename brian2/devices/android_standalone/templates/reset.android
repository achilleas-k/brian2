//// MAIN CODE /////////////////////////////////////////////////////////////

{% macro main() %}
    // USE_SPECIFIERS { _spikes }

    //// MAIN CODE ////////////
int run_{{codeobj_name}}() {
    const int _num_spikes  = _spikespace[_num_spikespace-1];
    for(int _index__spikes=0; _index_spikes<_num_spikes; _index_spikes++) {
        const int _neuron_idx = _spikespace[_index_spikes];
        const int _vectorisation_idx = _idx;
        {% for line in code_lines %}
        {{line}}
        {% endfor %}
    }
}
{% endmacro %}

////////////////////////////////////////////////////////////////////////////
//// SUPPORT CODE //////////////////////////////////////////////////////////

{% macro support_code() %}
    {% for line in support_code_lines %}
    {{line}}
    {% endfor %}
{% endmacro %}



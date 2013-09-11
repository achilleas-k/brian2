////////////////////////////////////////////////////////////////////////////
//// MAIN CODE /////////////////////////////////////////////////////////////

{% macro main() %}
    // USE_SPECIFIERS { _num_neurons, not_refractory, lastspike, t }
    ////// SUPPORT CODE ///////
    {% for line in support_code_lines %}
    // {{line}}
    {% endfor %}

int run_{{codeobj_name}}() {
    //// MAIN CODE ////////////
    long _numspikes = 0;
    for (int _idx=0; _idx<_num_idx; _idx++) {
        const int _vectorisation_idx = _idx;
        {% for line in code_lines %}
        {{line}}
        {% endfor %}
        if(_cond) {
            _spikespace[_numspikes++] = _idx;
            not_refractory[_idx] = false;
            lastspike[_idx] = t;
        }
        _spikespace[_num_idx] = _numspikes;
        return _numspikes;
    }
}
{% endmacro %}

////////////////////////////////////////////////////////////////////////////
//// SUPPORT CODE //////////////////////////////////////////////////////////

{% macro support_code() %}
    {% for line in support_code_lines %}
    // {{line}}
    {% endfor %}
{% endmacro %}




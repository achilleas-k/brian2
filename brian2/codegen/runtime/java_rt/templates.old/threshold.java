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
    {% for line in code_lines %}
    {{line}}
    {% endfor %}
    if(_cond) {
        _spikes_space.add(_idx);
        not_refractory[_idx] = false;
        lastspike[_idx] = t;
    }
    return_val = _spikes_space[_num_neurons];
{% endmacro %}

////////////////////////////////////////////////////////////////////////////
//// SUPPORT CODE //////////////////////////////////////////////////////////

{% macro support_code() %}
    {% for line in support_code_lines %}
    // {{line}}
    {% endfor %}
{% endmacro %}




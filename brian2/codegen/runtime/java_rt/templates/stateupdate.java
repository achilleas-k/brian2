//// MAIN CODE /////////////////////////////////////////////////////////////

{% macro main() %}
// USE_SPECIFIERS { _num_neurons }

////// SUPPORT CODE ///
{% for line in support_code_lines %}
//{{line}}
{% endfor %}

int32_t __attribute__((kernel)) update_{{codeobj_name}}(int32_t _idx) {
    const int _vectorisation_idx = _idx;
    {% for line in code_lines %}
    {{line}}
    {% endfor %}
    return _vectorisation_idx;
}

{% endmacro %}

////////////////////////////////////////////////////////////////////////////
//// SUPPORT CODE //////////////////////////////////////////////////////////

{% macro support_code() %}
	{% for line in support_code_lines %}
	{{line}}
	{% endfor %}
{% endmacro %}




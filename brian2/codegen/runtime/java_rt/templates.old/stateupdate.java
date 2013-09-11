//// MAIN CODE /////////////////////////////////////////////////////////////

{% macro main() %}
	// USE_SPECIFIERS { _num_neurons }

    ////// SUPPORT CODE ///
	{% for line in support_code_lines %}
	//{{line}}
	{% endfor %}

        {% for line in code_lines %}
        {{line}}
        {% endfor %}

{% endmacro %}

////////////////////////////////////////////////////////////////////////////
//// SUPPORT CODE //////////////////////////////////////////////////////////

{% macro support_code() %}
	{% for line in support_code_lines %}
	{{line}}
	{% endfor %}
{% endmacro %}




{% macro main() %}

    // USE_SPECIFIERS { _t, _clock_t, _indices }

    ////// SUPPORT CODE ///
	{% for line in support_code_lines %}
	//{{line}}
	{% endfor %}

    _t_data.add(_clock_t);

    // TODO: finish java version
    {% for _varname in _variable_names %}
    {
        for (int _idx=0; _idx < _num_indices; _idx++)
        {
            //final int _neuron_idx = _indices[_idx];
            //final int _vectorisation_idx = _neuron_idx;
            //{% for line in code_lines %}
            //{{line}}
            //{% endfor %}

            //// FIXME: This will not work for variables with other data types
            //double *recorded_entry = (double*)(_record_data->data + (_new_len - 1)*_record_strides[0] + _idx*_record_strides[1]);
            //*recorded_entry = _to_record_{{_varname}};
        }
    }
    {% endfor %}

{% endmacro %}

{% macro support_code() %}
{% for line in support_code_lines %}
{{line}}
{% endfor %}
{% endmacro %}


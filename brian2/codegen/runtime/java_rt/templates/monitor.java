{% macro main() %}
        // Assuming _t_arr and _i_arr are arraylists
        // Appending should be much more efficient than resizing arrays
        for(int _i=0; _i<_num_spikes; _i++)
	{
		_t_arr_data.add(t);
		_i_arr_data.add(_spikes[_i]);
	}
{% endmacro %}

{% macro support_code() %}
{% endmacro %}

{% macro main() %}
//**** arrays.rs ****//

// static arrays
{% for (varname, dtype_spec, N) in array_specs %}
{{dtype_spec}} *{{varname}};
const int _num_{{varname}} = {{N}};
{% endfor %}

// dynamic arrays
{% for (varname, dtype_spec) in dynamic_array_specs %}
std::vector<{{dtype_spec}}> {{varname}};
{% endfor %}

void _init_arrays()
{
	{% for (varname, dtype_spec, N) in array_specs %}
	{{varname}} = new {{dtype_spec}}[{{N}}];
	for(int i=0; i<{{N}}; i++) {{varname}}[i] = 0;
	{% endfor %}
}

void _dealloc_arrays()
{
	{% for (varname, dtype_spec, N) in array_specs %}
	if({{varname}}!=0)
	{
		delete [] {{varname}};
		{{varname}} = 0;
	}
	{% endfor %}
}

{% endmacro %}

/////////////////////////////////////////////////////////////////////////////////////////////////////


////////////////////////////////////////////////////////////////////////////
//// MAIN CODE /////////////////////////////////////////////////////////////

{% macro main() %}
//**** stateupdate.rs ****//
int32_t __attribute__((kernel)) update(int32_t _idx) {
    const int _vectorisation_idx = _idx;
    {% for line in code_lines %}
    {{line}}
    {% endfor %}
}
{% endmacro %}


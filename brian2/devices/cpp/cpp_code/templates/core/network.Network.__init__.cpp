Network {{objname}};
{% for o in args %}
{{objname}}.add({{o.name}});
{% endfor %}

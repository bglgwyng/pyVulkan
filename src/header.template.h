{% for i, j in typedefs.values() %}
typedef {{i}} {{j}};
{% endfor %}
{% for name, items in enums.items() %}
{% if items %}
typedef enum {{name}}{
{% for i in items %}
{% if loop.last %}
	{{i}} = {{items[i]}}
{% else %}
	{{i}} = {{items[i]}},
{% endif %}
{% endfor %}
} {{name}};
{% endif %}
{% endfor %}
{% for _, i in funcpointers.items() %}
{{i.replace('VKAPI_PTR ', vkapi_ptr)}}
{% endfor %}
{% for name, (type_, fields) in struct_unions.items() %}
typedef {{type_}} {{name}}{
{% for type_, name, enum in fields %}
{% if enum %}
	{{type_}} {{name}}[{{macros[enum]}}];
{% else %}
	{{type_}} {{name}};
{% endif %}
{% endfor %}
} {{name}};
{% endfor %}
{% for name, (type_, name, params, _) in funcs.items() %}
{% if name in extensions %}
typedef {{type_}} ({{vkapi_ptr}}*PFN_{{name}})({{', '.join(params)}});
{% else %}
{{type_}} {{name}}({{', '.join(params)}});
{% endif %}
{% endfor %}

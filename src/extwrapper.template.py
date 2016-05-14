from ._vulkan import ffi, _callApi, _raiseException

{% for i, (exception_handler, result, result_length, args, inner_args, new_vars) in exts.items() %}
def {{i}}Wrapper(fn):
	fn = ffi.cast('PFN_{{i}}', fn)
	def {{i}}({% for j, k in args %}{{j}}, {% endfor %}):
{% for i in new_vars %}
		{{i}} = ffi.new('{{new_vars[i]}}')
{% endfor %}
{% if result_length and result_length!=1 %}
		ret = _callApi(fn, {% for j in inner_args[:-1] %}{{j}}, {% endfor %}ffi.NULL)
{% if exception_handler %}
		_raiseException(ret)
{% endif %}
		{{result[0]}} = ffi.new('{{result[1].item.cname}}[]', {{result_length}}[0])
{% endif %}
		ret = _callApi(fn, {% for j in inner_args %}{{j}}, {% endfor %})
{% if exception_handler %}
		_raiseException(ret)
{% endif %}
{% if result %}
		return {{result[0]}}{% if result_length==1 %}[0]{% endif %}
		
{% endif %}
	return {{i}}

{% endfor %}

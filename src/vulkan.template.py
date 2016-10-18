import cffi as _cffi
import pkg_resources as _pkg_resources
import collections as _collections
import weakref as _weakref
import sys

class PlatformNotSupportedError(Exception):
	pass

class ProcedureNotFoundError(Exception):
	pass

class ExtensionNotSupportedError(Exception):
	pass

ffi = _cffi.FFI()

_weakkey_dict = _weakref.WeakKeyDictionary()

def _castToPtr2(x, _type):
	if isinstance(x, ffi.CData):
		if _type.item==ffi.typeof(x):
			return ffi.addressof(x)
		return x
	if isinstance(x, _collections.Iterable):
		if _type.item.kind=='pointer':
			ptrs = [_castToPtr(i, _type.item) for i in x]
			ret = ffi.new(_type.item.cname+'[]', ptrs)
			_weakkey_dict[ret] = tuple(ptrs)
			return ret
		else:
			return ffi.new(_type.item.cname+'[]', x)
	return ffi.cast(_type, x)

def _castToPtr3(x, _type):
	if isinstance(x, str):
		x = x.encode('ascii')
	return _castToPtr2(x, _type)

if sys.version_info<(3, 0):
	def _cdef(header):
		ffi.cdef(_pkg_resources.resource_string(__name__, header))
	_castToPtr = _castToPtr2
else:
	def _cdef(header):
		ffi.cdef(_pkg_resources.resource_string(__name__, header).decode())
	_castToPtr = _castToPtr3

if sys.platform=='win32':
	_cdef('vulkan_win32_cffi.h')
	_lib = ffi.dlopen('vulkan-1.dll')
elif sys.platform.startswith('linux'):
	_cdef('vulkan_linux_cffi.h')
	_lib = ffi.dlopen('libvulkan.so')
else:
	raise PlatformNotSupportedError()

def _new(ctype, **kwargs):
	_type = ffi.typeof(ctype)
	kwargs = {k:kwargs[k] for k in kwargs if kwargs[k]}
	ptrs = {k:_castToPtr(kwargs[k], dict(_type.fields)[k].type) for k in kwargs if dict(_type.fields)[k].type.kind=='pointer'}
	ret = ffi.new(_type.cname+'*', dict(kwargs, **ptrs))[0]
	_weakkey_dict[ret] = tuple(ptrs.values())
	return ret

class VkException(Exception):
	pass

class VkError(Exception):
	pass

{% for i in exceptions %}
class {{i}}(VkException):
	pass
{% endfor %}

{% for i in errors %}
class {{i}}(VkError):
	pass
{% endfor %}

def _raiseException(result):
	exception_codes = {
{% for i, j in exceptions.items() %}
		{{i}}:{{j}},
{% endfor %}
{% for i, j in errors.items() %}
{% if loop.last %}
		{{i}}:{{j}}
{% else %}
		{{i}}:{{j}},
{% endif %}
{% endfor %}
	}
	raise exception_codes[result]

def _callApi(fn, *args):
	def _(x, _type):
		if x is None:
			return ffi.NULL
		if _type.kind=='pointer':
			return _castToPtr(x, _type)
		return x

	return fn(*(_(i, j) for i, j in zip(args, ffi.typeof(fn).args)))

def vkGetInstanceProcAddr(instance, pName):
	fn = _callApi(_lib.vkGetInstanceProcAddr, instance, pName)
	if fn==ffi.NULL:
		raise ProcedureNotFoundError()
	if not pName in _instance_ext_funcs:
		raise ExtensionNotSupportedError()
	fn = ffi.cast('PFN_'+pName, fn)
	return _instance_ext_funcs[pName](fn)

def vkGetDeviceProcAddr(device, pName):
	fn = _callApi(_lib.vkGetDeviceProcAddr, device, pName)
	if fn==ffi.NULL:
		raise ProcedureNotFoundError()
	if not pName in _device_ext_funcs:
		raise ExtensionNotSupportedError()
	fn = ffi.cast('PFN_'+pName, fn)
	return _device_ext_funcs[pName](fn)

def VK_MAKE_VERSION(major, minor, patch):
	return (((major) << 22) | ((minor) << 12) | (patch))

def VK_VERSION_MAJOR(version):
	return version>>22

def VK_VERSION_MINOR(version):
	return (version>>12)&0x3ff

def VK_VERSION_PATCH(version):
	return version&0xfff

VK_API_VERSION = VK_MAKE_VERSION(1, 0, 0)
VK_API_VERSION_1_0 = VK_MAKE_VERSION(1, 0, 0)

VK_NULL_HANDLE = 0

{% for _, i in enums.items() %}
{% for name, value in i.items() %}
{{name}} = {{value}}
{% endfor %}
{% endfor %}

{% for i, _ in funcpointers.items() %}
{{i[4:]}} = ffi.callback('{{i}}')
{% endfor %}

{% for i, (wrapper_params, call_params, len_autos) in constructors.items() %}

def {{i}}({{wrapper_params}}):
{% for j, k in len_autos %}
	if {{j}} is None:
{% if len(k)>1 %}
		assert {{'=='.join(k)}}
{% endif %}
		{{j}} = {{k[0]}}
{% endfor %}
	return _new('{{i}}', {{call_params}})
{% endfor %}

{% macro def_func_return_single(i, fn) %}
{% set passed_params = func_wrappers[i][2][:-1] %}
{% set ptr_param = func_wrappers[i][2][-1] %}
def {{i}}({{', '.join(passed_params)}}):
	{{ptr_param}} = ffi.new('{{func_wrappers[i][1][-1]}}')
{% if i in throwable_funcs %}
	result = _callApi({{fn}}, {{', '.join(passed_params+[ptr_param])}})
	if result!=VK_SUCCESS:
		raise _raiseException[result]
{% else %}
	_callApi({{fn}}, {{', '.join(passed_params+[ptr_param])}})
{% endif %}
	return {{func_wrappers[i][2][-1]}}[0]
{% endmacro %}

{% macro def_func_return_list(i, fn) %}
{% set passed_params = func_wrappers[i][2][:-2] %}
{% set len_param = func_wrappers[i][2][-2] %}
{% set ptr_param = func_wrappers[i][2][-1] %}
def {{i}}({{', '.join(passed_params)}}):
	{{len_param}} = ffi.new('{{func_wrappers[i][1][-2]}}')
{% if i in throwable_funcs %}
	result = _callApi({{fn}}, {{', '.join(func_wrappers[i][2][:-2]+[len_param, 'ffi.NULL'])}})
	if result!=VK_SUCCESS:
		raise _raiseException[result]
{% else %}
	_callApi({{fn}}, {{', '.join(func_wrappers[i][2][:-2]+[len_param, 'ffi.NULL'])}})
{% endif %}
	{{ptr_param}} = ffi.new('{{func_wrappers[i][1][-1][:-1] if func_wrappers[i][1][-1][-1]=='*'}}[]', {{len_param}}[0])
{% if i in throwable_funcs %}
	result = _callApi({{fn}}, {{', '.join(passed_params+[len_param, ptr_param])}})
	if result!=VK_SUCCESS:
		raise _raiseException[result]
{% else %}
	_callApi({{fn}}, {{', '.join(passed_params+[len_param, ptr_param])}})
{% endif %}
	return {{func_wrappers[i][2][-1]}}
{% endmacro %}

{% macro def_func_return_list_len_specified(i, fn) %}
{% set passed_params = func_wrappers[i][2][:-1] %}
{% set ptr_param = func_wrappers[i][2][-1] %}
def {{i}}({{', '.join(passed_params)}}):
	{{ptr_param}} = ffi.new('{{func_wrappers[i][1][-1]}}')
{% if i in throwable_funcs %}
	result = _callApi({{fn}}, {{', '.join(passed_params+[ptr_param])}})
	if result!=VK_SUCCESS:
		raise _raiseException[result]
{% else %}
	_callApi({{fn}}, {{', '.join(passed_params+[ptr_param])}})
{% endif %}
	return {{func_wrappers[i][2][-1]}}
{% endmacro %}


{% macro def_func_return_nothing(i, fn) %}
{% set passed_params = func_wrappers[i][2] %}
def {{i}}({{', '.join(passed_params)}}):
{% if i in throwable_funcs %}
	result = _callApi({{fn}}, {{', '.join(passed_params)}})
	if result!=VK_SUCCESS:
		raise _raiseException[result]
{% else %}
	_callApi(_lib.{{i}}, {{', '.join(passed_params)}})
{% endif %}
{% endmacro %}

{% macro def_funcs(funcs, def_macro) %}
{% for i in funcs %}
{% if i in all_extensions %}
def _wrap_{{i}}(fn):
{{def_macro(i, 'fn')|indent(4, True)}}
    return {{i}}
{% else %}
{{def_macro(i, '_lib.'+i)}}
{% endif %}
{% endfor %}
{% endmacro %}

{{ def_funcs(funcs_return_single, def_func_return_single)}}
{{ def_funcs(funcs_return_list, def_func_return_list)}}
{{ def_funcs(funcs_return_list_len_specified, def_func_return_list_len_specified)}}
{{ def_funcs(funcs_return_nothing, def_func_return_nothing)}}

_instance_ext_funcs = {
{% for i in instance_ext_funcs %}
{% if loop.last %}
	'{{i}}':_wrap_{{i}}
{% else %}
	'{{i}}':_wrap_{{i}},
{% endif %}
{% endfor %}
    }

_device_ext_funcs = {
{% for i in device_ext_funcs %}
{% if loop.last %}
	'{{i}}':_wrap_{{i}}
{% else %}
	'{{i}}':_wrap_{{i}},
{% endif %}
{% endfor %}
    }

{% for name, value in macros.items() %}
{{name}} = {{value}}
{% endfor %}

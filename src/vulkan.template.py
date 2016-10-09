import cffi as _cffi
import pkg_resources as _pkg_resources
import collections as _collections
import weakref as _weakref
import sys

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
	ffi.cdef(_pkg_resources.resource_string(__name__, "_vulkan.h"))
	_castToPtr = _castToPtr2
else:
	ffi.cdef(_pkg_resources.resource_string(__name__, "_vulkan.h").decode())
	_castToPtr = _castToPtr3

if sys.platform=='win32':
	_lib = ffi.dlopen('vulkan-1.dll')

	PFN_vkDebugReportCallbackEXT = ffi.callback('VkBool32 __stdcall(VkFlags, VkDebugReportObjectTypeEXT, uint64_t, size_t, int32_t, const char *, const char *, void *)')
	PFN_vkAllocationFunction = ffi.callback('void* __stdcall(void*, size_t, size_t, VkSystemAllocationScope)')
	PFN_vkReallocationFunction = ffi.callback('void* __stdcall(void*, void*, size_t, size_t, VkSystemAllocationScope)')
	PFN_vkFreeFunction = ffi.callback('void __stdcall(void*, void*)')
	PFN_vkInternalAllocationNotification = ffi.callback('void __stdcall(void*, size_t, VkInternalAllocationType, VkSystemAllocationScope)')
	PFN_vkInternalFreeNotification = PFN_vkInternalAllocationNotification

else:
	_lib = ffi.dlopen('libvulkan.so')

	PFN_vkDebugReportCallbackEXT = ffi.callback('VkBool32(VkFlags, VkDebugReportObjectTypeEXT, uint64_t, size_t, int32_t, const char *, const char *, void *)')
	PFN_vkAllocationFunction = ffi.callback('void*(void*, size_t, size_t, VkSystemAllocationScope)')
	PFN_vkReallocationFunction = ffi.callback('void*(void*, void*, size_t, size_t, VkSystemAllocationScope)')
	PFN_vkFreeFunction = ffi.callback('void(void*, void*)')
	PFN_vkInternalAllocationNotification = ffi.callback('void(void*, size_t, VkInternalAllocationType, VkSystemAllocationScope)')
	PFN_vkInternalFreeNotification = PFN_vkInternalAllocationNotification

{% for i in enums %}
{% for k, v in enums[i].relements.items() %}{{k}} = {{v}}
{% endfor %}

{% endfor %}

def _newStruct(ctype, **kwargs):
	_type = ffi.typeof(ctype)

	kwargs = {k:kwargs[k] for k in kwargs if kwargs[k]}
	ptrs = {k:_castToPtr(kwargs[k], dict(_type.fields)[k].type) for k in kwargs if dict(_type.fields)[k].type.kind=='pointer'}

	ret = ffi.new(_type.cname+'*', dict(kwargs, **ptrs))[0]

	_weakkey_dict[ret] = tuple(ptrs.values())

	return ret

{% for i, fields in structs.items() %}

def {{i}}({% for j, _ in fields %}{{j}} = {% if j in field_defaults %}{{field_defaults[j](i)}}{% else %}None{% endif %}, {% endfor %}):
	return _newStruct('{{i}}', {% for j, _ in fields %}{{j}} = {{j}}, {% endfor %})
{% endfor %}

class VkException(Exception):
	pass

class VkError(Exception):
	pass

{% for _, i ,j in exceptions %}
class {{i}}({{j}}):
	pass

{% endfor %}

def _raiseException(ret):
	exceptions = {
	{% for i, j, _ in exceptions %}
		{{i}}:{{j}},
	{% endfor %}
	}

	if ret!=0:
		raise exceptions[ret]

def _callApi(fn, *args):
	def _(x, _type):
		if x is None:
			return ffi.NULL
		if _type.kind=='pointer':
			return _castToPtr(x, _type)
		return x

	return fn(*(_(i, j) for i, j in zip(args, ffi.typeof(fn).args)))


{% for i, (exception_handler, result, result_length, args, inner_args, new_vars) in funcs.items() %}
if hasattr(_lib, '{{i}}'):
	def {{i}}({% for j, k in args %}{{j}}, {% endfor %}):
{% for i in new_vars %}
		{{i}} = ffi.new('{{new_vars[i]}}')
{% endfor %}
{% if result_length and result_length!=1 %}
		ret = _callApi(_lib.{{i}}, {% for j in inner_args[:-1] %}{{j}}, {% endfor %}ffi.NULL)
{% if exception_handler %}
		_raiseException(ret)
{% endif %}
		{{result[0]}} = ffi.new('{{result[1].item.cname}}[]', {{result_length}}[0])
{% endif %}
		ret = _callApi(_lib.{{i}}, {% for j in inner_args %}{{j}}, {% endfor %})
{% if exception_handler %}
		_raiseException(ret)
{% endif %}
{% if result %}
		return {{result[0]}}{% if result_length==1 %}[0]{% endif %}{% endif %}


{% endfor %}

{% for i, (exception_handler, result, result_length, args, inner_args, new_vars) in exts.items() %}
def _{{i}}Wrapper(fn):
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

def vkGetInstanceProcAddr(instance, pName, ):

	ret = _callApi(_lib.vkGetInstanceProcAddr, instance, pName, )
	return globals()["_%sWrapper"%pName](ret)

def vkGetDeviceProcAddr(device, pName, ):

	ret = _callApi(_lib.vkGetDeviceProcAddr, device, pName, )
	return globals()["_%sWrapper"%pName](ret)

{% for name, value in macros %}
{{name}} = {{value}}
{% endfor %}

def VK_MAKE_VERSION(major, minor, patch):
	return (((major) << 22) | ((minor) << 12) | (patch))

def VK_VERSION_PATCH(version):
	return version&0xfff

def VK_VERSION_MINOR(version):
	return (version>>12)&0x3ff

def VK_VERSION_MAJOR(version):
	return version>>22

from cffi import *
from pkg_resources import *
from collections import Iterable
from weakref import *
import sys

ffi = FFI()

_weakkey_dict = WeakKeyDictionary()

def _castToPtr2(x, _type):
	if isinstance(x, ffi.CData):
		if _type.item==ffi.typeof(x):
			return ffi.addressof(x)
		return x
	if isinstance(x, Iterable):
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
	ffi.cdef(resource_string(__name__, "_vulkan.h"))
	_castToPtr = _castToPtr2
else:
	ffi.cdef(resource_string(__name__, "_vulkan.h").decode())
	_castToPtr = _castToPtr3

if sys.platform=='win32':
	_lib = ffi.dlopen('vulkan-1.dll')
else:
	_lib = ffi.dlopen('libvulkan.so')

{% for i in enums %}
class {{i}}:
	{% for k, v in enums[i].relements.items() %}{{k}} = {{v}}
	{% endfor %}

{% for k, v in enums[i].relements.items() %}
{{k}} = {{i}}.{{k}}
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


def vkGetInstanceProcAddr(instance, pName, ):

	ret = _callApi(_lib.vkGetInstanceProcAddr, instance, pName, )
	return ret

def vkGetDeviceProcAddr(device, pName, ):

	ret = _callApi(_lib.vkGetDeviceProcAddr, device, pName, )
	return ret

VK_KHR_SAMPLER_MIRROR_CLAMP_TO_EDGE_EXTENSION_NAME = "VK_KHR_sampler_mirror_clamp_to_edge"
VK_KHR_SURFACE_EXTENSION_NAME = "VK_KHR_surface"
VK_KHR_sampler_mirror_clamp_to_edge = 1
VK_KHR_SWAPCHAIN_EXTENSION_NAME = "VK_KHR_swapchain"

def VK_MAKE_VERSION(major, minor, patch):
	return (((major) << 22) | ((minor) << 12) | (patch))

VULKAN_H_ = 1
VK_ATTACHMENT_UNUSED = -1

def VK_VERSION_PATCH(version):
	return version&0xfff

VK_WHOLE_SIZE = -1
VK_UUID_SIZE = 16
VK_REMAINING_MIP_LEVELS = -1
VK_MAX_MEMORY_TYPES = 32
VK_FALSE = 0
VK_KHR_SURFACE_SPEC_VERSION = 25
VK_KHR_display_swapchain = 1
VK_TRUE = 1
VK_NV_GLSL_SHADER_SPEC_VERSION = 1
VK_NV_GLSL_SHADER_EXTENSION_NAME = "VK_NV_glsl_shader"
VK_EXT_debug_report = 1
VK_EXT_DEBUG_REPORT_SPEC_VERSION = 2
VK_KHR_display = 1
VK_STRUCTURE_TYPE_DEBUG_REPORT_CREATE_INFO_EXT = VK_STRUCTURE_TYPE_DEBUG_REPORT_CALLBACK_CREATE_INFO_EXT
VK_KHR_surface = 1
VK_KHR_SAMPLER_MIRROR_CLAMP_TO_EDGE_SPEC_VERSION = 1
VK_API_VERSION = VK_MAKE_VERSION(1, 0, 5)
VK_MAX_EXTENSION_NAME_SIZE = 256

def VK_VERSION_MINOR(version):
	return (version>>12)&0x3ff

VK_QUEUE_FAMILY_IGNORED = -1

def VK_VERSION_MAJOR(version):
	return version>>22

VK_KHR_DISPLAY_SWAPCHAIN_SPEC_VERSION = 9
VK_LOD_CLAMP_NONE = 1000.0
VK_KHR_DISPLAY_SPEC_VERSION = 21
VK_NULL_HANDLE = 0
VK_MAX_PHYSICAL_DEVICE_NAME_SIZE = 256
VK_REMAINING_ARRAY_LAYERS = -1
VK_KHR_SWAPCHAIN_SPEC_VERSION = 67
VK_VERSION_1_0 = 1
VK_MAX_DESCRIPTION_SIZE = 256
VK_KHR_DISPLAY_SWAPCHAIN_EXTENSION_NAME = "VK_KHR_display_swapchain"
VK_KHR_swapchain = 1
VK_EXT_DEBUG_REPORT_EXTENSION_NAME = "VK_EXT_debug_report"
VK_MAX_MEMORY_HEAPS = 16
VK_SUBPASS_EXTERNAL = -1
VK_NV_glsl_shader = 1
VK_KHR_DISPLAY_EXTENSION_NAME = "VK_KHR_display"


VK_KHR_xlib_surface = 1
VK_KHR_XLIB_SURFACE_SPEC_VERSION = 6
VK_KHR_XLIB_SURFACE_EXTENSION_NAME = "VK_KHR_xlib_surface"

VK_KHR_xcb_surface = 1
VK_KHR_XCB_SURFACE_SPEC_VERSION = 6
VK_KHR_XCB_SURFACE_EXTENSION_NAME = "VK_KHR_xcb_surface"

VK_KHR_wayland_surface = 1
VK_KHR_WAYLAND_SURFACE_SPEC_VERSION = 5
VK_KHR_WAYLAND_SURFACE_EXTENSION_NAME = "VK_KHR_wayland_surface"

VK_KHR_mir_surface = 1
VK_KHR_MIR_SURFACE_SPEC_VERSION = 4
VK_KHR_MIR_SURFACE_EXTENSION_NAME = "VK_KHR_mir_surface"

VK_KHR_android_surface = 1
VK_KHR_ANDROID_SURFACE_SPEC_VERSION = 6
VK_KHR_ANDROID_SURFACE_EXTENSION_NAME = "VK_KHR_android_surface"

VK_KHR_win32_surface = 1
VK_KHR_WIN32_SURFACE_SPEC_VERSION = 5
VK_KHR_WIN32_SURFACE_EXTENSION_NAME = "VK_KHR_win32_surface"
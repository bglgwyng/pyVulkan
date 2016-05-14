from pycparser import parse_file, c_ast, c_generator
from cffi import *

header_path  = '_vulkan.h'

ffi = FFI()
ffi.cdef(open(header_path).read())

lib = ffi.dlopen('libvulkan.so')

ast = parse_file(header_path, use_cpp = True)

funcs_with_return = [
	'vkAcquireNextImageKHR',
	'vkAllocateMemory',
	'vkCreateBuffer',
	'vkCreateBufferView',
	'vkCreateCommandPool',
	'vkCreateDescriptorPool',
	'vkCreateDescriptorSetLayout',
	'vkCreateDevice',
	'vkCreateDisplayModeKHR',
	'vkCreateDisplayPlaneSurfaceKHR',
	'vkCreateEvent',
	'vkCreateFence',
	'vkCreateFramebuffer',
	'vkCreateImage',
	'vkCreateImageView',
	'vkCreateInstance',
	'vkCreatePipelineCache',
	'vkCreatePipelineLayout',
	'vkCreateQueryPool',
	'vkCreateRenderPass',
	'vkCreateSampler',
	'vkCreateSemaphore',
	'vkCreateShaderModule',
	'vkCreateSwapchainKHR',
	'vkGetBufferMemoryRequirements',
	'vkGetDeviceMemoryCommitment',
	'vkGetDeviceQueue',
	'vkGetDisplayPlaneCapabilitiesKHR',
	'vkGetImageMemoryRequirements',
	'vkGetImageSubresourceLayout',
	'vkGetPhysicalDeviceFeatures',
	'vkGetPhysicalDeviceFormatProperties',
	'vkGetPhysicalDeviceImageFormatProperties',
	'vkGetPhysicalDeviceMemoryProperties',
	'vkGetPhysicalDeviceProperties',
	'vkGetRenderAreaGranularity',
	'vkMapMemory',
	'vkGetPhysicalDeviceSurfaceSupportKHR',
	'vkGetPhysicalDeviceSurfaceCapabilitiesKHR',
	
	'vkCreateXlibSurfaceKHR',
	'vkCreateXcbSurfaceKHR',
	'vkCreateMirSurfaceKHR'
	'vkCreateAndroidSurfaceKHR'
	'vkCreateWin32SurfaceKHR']

funcs_with_return_as_list =[
	'vkAllocateCommandBuffers',
	'vkAllocateDescriptorSets'

	'vkCreateSharedSwapchainsKHR',
	'vkCreateDebugReportCallbackEXT']

funcs_with_count_return = [
	'vkGetDisplayModePropertiesKHR',
	'vkGetDisplayPlaneSupportedDisplaysKHR',
	'vkGetImageSparseMemoryRequirements',
	'vkGetPhysicalDeviceDisplayPlanePropertiesKHR',
	'vkGetPhysicalDeviceDisplayPropertiesKHR',
	'vkGetPhysicalDeviceQueueFamilyProperties',
	'vkGetPhysicalDeviceSparseImageFormatProperties',
	'vkGetPhysicalDeviceSurfaceFormatsKHR',
	'vkGetPhysicalDeviceSurfacePresentModesKHR',
	'vkGetSwapchainImagesKHR',
	'vkEnumerateInstanceExtensionProperties',
	'vkEnumerateDeviceExtensionProperties',
	'vkEnumerateInstanceLayerProperties',
	'vkEnumerateDeviceLayerProperties',
	'vkEnumerateDeviceExtensionProperties',
	'vkEnumerateDeviceLayerProperties',
	'vkEnumerateInstanceExtensionProperties',
	'vkEnumerateInstanceLayerProperties',
	'vkEnumeratePhysicalDevices']


def genExceptions():
	enums = [
		'VK_NOT_READY',
	    'VK_TIMEOUT',
	    'VK_EVENT_SET',
	    'VK_EVENT_RESET',
	    'VK_INCOMPLETE',
	    'VK_ERROR_OUT_OF_HOST_MEMORY',
	    'VK_ERROR_OUT_OF_DEVICE_MEMORY',
	    'VK_ERROR_INITIALIZATION_FAILED',
	    'VK_ERROR_DEVICE_LOST',
	    'VK_ERROR_MEMORY_MAP_FAILED',
	    'VK_ERROR_LAYER_NOT_PRESENT',
	    'VK_ERROR_EXTENSION_NOT_PRESENT',
	    'VK_ERROR_FEATURE_NOT_PRESENT',
	    'VK_ERROR_INCOMPATIBLE_DRIVER',
	    'VK_ERROR_TOO_MANY_OBJECTS',
	    'VK_ERROR_FORMAT_NOT_SUPPORTED',
	    'VK_ERROR_SURFACE_LOST_KHR',
	    'VK_ERROR_NATIVE_WINDOW_IN_USE_KHR',
	    'VK_SUBOPTIMAL_KHR',
	    'VK_ERROR_OUT_OF_DATE_KHR',
	    'VK_ERROR_INCOMPATIBLE_DISPLAY_KHR',
	    'VK_ERROR_VALIDATION_FAILED_EXT',
	    'VK_ERROR_INVALID_SHADER_NV']

	def __(x):
		def _(x):
			if x in ('KHR', 'EXT', 'NV'):
				return x
			return x[0]+x[1:].lower()
		return ''.join([_(i) for i in x.split('_')])
	def _(x):
		if x.startswith('VK_ERROR'):
			return (x, 'Vk%sError'%__(x[9:]), 'VkError')
		else:
			return (x, 'Vk%sException'%__(x[3:]), 'VkException')
	
	return [_(i) for i in enums]

types = {}
structs = {}
enums = {}
funcs = {}
exts = {}

generator = c_generator.CGenerator()

class Visitor(c_ast.NodeVisitor):

	def visit_FileAST(self, node):

		named = set()

		for i, v in node.children():
			if isinstance(v.type, c_ast.TypeDecl):

				if v.name.startswith('Vk'):
					_type = ffi.typeof(v.name)
					
					if _type.kind=='primitive':
						pass
					elif  _type.kind=='struct':
						if _type.fields:
							structs[v.name] = _type.fields
					elif  _type.kind=='union':
						if _type.fields:					
							structs[v.name] = _type.fields
					elif _type.kind=='enum':
						enums[v.name] = _type
					
			elif isinstance(v.type, c_ast.FuncDecl):
				if not v.name.startswith('vk'):
					continue
				_type = ffi.typeof('PFN_'+v.name)
				
				_, funcdecl = v.children()[0]

				inner_args = [i.name for _, i in funcdecl.args.children()]
				args = zip(inner_args, _type.args)

				if _type.result.cname=='VkResult':
					exception_handler = True
				else:
					exception_handler = False

				new_vars = {}

				result_length = None

				if _type.result.cname not in ('void', 'VkResult'):
					result = ('ret',)
				else:
					if v.name in funcs_with_return:
						result = args[-1]
						result_length = 1
						new_vars[result[0]] = "%s"%result[1].cname
						args = args[:-1]
					elif v.name in funcs_with_return_as_list:
						result = args[-1]
						new_vars[result[0]] = "%s"%result[1].cname
						args = args[:-1]
					elif v.name in funcs_with_count_return:
						result = args[-1]
						result_length = args[-2][0]
						new_vars[args[-2][0]] = "%s"%args[-2][1].cname
						args = args[:-2]
					else:
						result = None

				tmp = (exception_handler, result, result_length, args, inner_args, new_vars)
				if v.name[-1].isupper():
					exts[v.name] = tmp
				else:
					funcs[v.name] = tmp
				continue
				
Visitor().visit(ast)

def gensType(x):
	tmp = ''
	postfix = ''
	for i in ('KHR', 'EXT', 'NV'):
		if x.endswith(i):
			postfix = '_'+i
			x = x[:-len(i)]

	for i in x[2:]:
		if i.isupper():
			tmp += '_'+i
		else:
			tmp += i.upper()
	return 'VK_STRUCTURE_TYPE'+tmp+postfix

from jinja2 import *
import os
env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))), trim_blocks = True)

genvulkan = env.get_template('vulkan.template.py')
with open('../pyVulkan/_vulkan.py', 'w') as f:
	f.write(genvulkan.render(structs = structs, field_defaults = {'sType':gensType}, enums = enums, exceptions = genExceptions(), funcs = funcs))

genextwrapper = env.get_template('extwrapper.template.py')
with open('../pyVulkan/extwrapper.py', 'w') as f:
	f.write(genextwrapper.render(exts = exts))
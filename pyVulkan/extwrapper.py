from ._vulkan import ffi, _callApi, _raiseException

def vkDestroySurfaceKHRWrapper(fn):
	fn = ffi.cast('PFN_vkDestroySurfaceKHR', fn)
	def vkDestroySurfaceKHR(instance, surface, pAllocator, ):
		ret = _callApi(fn, instance, surface, pAllocator, )
	return vkDestroySurfaceKHR

def vkGetPhysicalDeviceSurfaceSupportKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceSurfaceSupportKHR', fn)
	def vkGetPhysicalDeviceSurfaceSupportKHR(physicalDevice, queueFamilyIndex, surface, ):
		pSupported = ffi.new('unsigned int *')
		ret = _callApi(fn, physicalDevice, queueFamilyIndex, surface, pSupported, )
		_raiseException(ret)
		return pSupported[0]		
	return vkGetPhysicalDeviceSurfaceSupportKHR

def vkGetPhysicalDeviceSurfaceCapabilitiesKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceSurfaceCapabilitiesKHR', fn)
	def vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice, surface, ):
		pSurfaceCapabilities = ffi.new('VkSurfaceCapabilitiesKHR *')
		ret = _callApi(fn, physicalDevice, surface, pSurfaceCapabilities, )
		_raiseException(ret)
		return pSurfaceCapabilities[0]		
	return vkGetPhysicalDeviceSurfaceCapabilitiesKHR

def vkGetPhysicalDeviceSurfaceFormatsKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceSurfaceFormatsKHR', fn)
	def vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice, surface, ):
		pSurfaceFormatCount = ffi.new('unsigned int *')
		ret = _callApi(fn, physicalDevice, surface, pSurfaceFormatCount, ffi.NULL)
		_raiseException(ret)
		pSurfaceFormats = ffi.new('VkSurfaceFormatKHR[]', pSurfaceFormatCount[0])
		ret = _callApi(fn, physicalDevice, surface, pSurfaceFormatCount, pSurfaceFormats, )
		_raiseException(ret)
		return pSurfaceFormats		
	return vkGetPhysicalDeviceSurfaceFormatsKHR

def vkGetPhysicalDeviceSurfacePresentModesKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceSurfacePresentModesKHR', fn)
	def vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice, surface, ):
		pPresentModeCount = ffi.new('unsigned int *')
		ret = _callApi(fn, physicalDevice, surface, pPresentModeCount, ffi.NULL)
		_raiseException(ret)
		pPresentModes = ffi.new('VkPresentModeKHR[]', pPresentModeCount[0])
		ret = _callApi(fn, physicalDevice, surface, pPresentModeCount, pPresentModes, )
		_raiseException(ret)
		return pPresentModes		
	return vkGetPhysicalDeviceSurfacePresentModesKHR

def vkCreateSwapchainKHRWrapper(fn):
	fn = ffi.cast('PFN_vkCreateSwapchainKHR', fn)
	def vkCreateSwapchainKHR(device, pCreateInfo, pAllocator, ):
		pSwapchain = ffi.new('struct VkSwapchainKHR_T * *')
		ret = _callApi(fn, device, pCreateInfo, pAllocator, pSwapchain, )
		_raiseException(ret)
		return pSwapchain[0]		
	return vkCreateSwapchainKHR

def vkDestroySwapchainKHRWrapper(fn):
	fn = ffi.cast('PFN_vkDestroySwapchainKHR', fn)
	def vkDestroySwapchainKHR(device, swapchain, pAllocator, ):
		ret = _callApi(fn, device, swapchain, pAllocator, )
	return vkDestroySwapchainKHR

def vkGetSwapchainImagesKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetSwapchainImagesKHR', fn)
	def vkGetSwapchainImagesKHR(device, swapchain, ):
		pSwapchainImageCount = ffi.new('unsigned int *')
		ret = _callApi(fn, device, swapchain, pSwapchainImageCount, ffi.NULL)
		_raiseException(ret)
		pSwapchainImages = ffi.new('struct VkImage_T *[]', pSwapchainImageCount[0])
		ret = _callApi(fn, device, swapchain, pSwapchainImageCount, pSwapchainImages, )
		_raiseException(ret)
		return pSwapchainImages		
	return vkGetSwapchainImagesKHR

def vkAcquireNextImageKHRWrapper(fn):
	fn = ffi.cast('PFN_vkAcquireNextImageKHR', fn)
	def vkAcquireNextImageKHR(device, swapchain, timeout, semaphore, fence, ):
		pImageIndex = ffi.new('unsigned int *')
		ret = _callApi(fn, device, swapchain, timeout, semaphore, fence, pImageIndex, )
		_raiseException(ret)
		return pImageIndex[0]		
	return vkAcquireNextImageKHR

def vkQueuePresentKHRWrapper(fn):
	fn = ffi.cast('PFN_vkQueuePresentKHR', fn)
	def vkQueuePresentKHR(queue, pPresentInfo, ):
		ret = _callApi(fn, queue, pPresentInfo, )
		_raiseException(ret)
	return vkQueuePresentKHR

def vkGetPhysicalDeviceDisplayPropertiesKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceDisplayPropertiesKHR', fn)
	def vkGetPhysicalDeviceDisplayPropertiesKHR(physicalDevice, ):
		pPropertyCount = ffi.new('unsigned int *')
		ret = _callApi(fn, physicalDevice, pPropertyCount, ffi.NULL)
		_raiseException(ret)
		pProperties = ffi.new('VkDisplayPropertiesKHR[]', pPropertyCount[0])
		ret = _callApi(fn, physicalDevice, pPropertyCount, pProperties, )
		_raiseException(ret)
		return pProperties		
	return vkGetPhysicalDeviceDisplayPropertiesKHR

def vkGetPhysicalDeviceDisplayPlanePropertiesKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceDisplayPlanePropertiesKHR', fn)
	def vkGetPhysicalDeviceDisplayPlanePropertiesKHR(physicalDevice, ):
		pPropertyCount = ffi.new('unsigned int *')
		ret = _callApi(fn, physicalDevice, pPropertyCount, ffi.NULL)
		_raiseException(ret)
		pProperties = ffi.new('VkDisplayPlanePropertiesKHR[]', pPropertyCount[0])
		ret = _callApi(fn, physicalDevice, pPropertyCount, pProperties, )
		_raiseException(ret)
		return pProperties		
	return vkGetPhysicalDeviceDisplayPlanePropertiesKHR

def vkGetDisplayPlaneSupportedDisplaysKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetDisplayPlaneSupportedDisplaysKHR', fn)
	def vkGetDisplayPlaneSupportedDisplaysKHR(physicalDevice, planeIndex, ):
		pDisplayCount = ffi.new('unsigned int *')
		ret = _callApi(fn, physicalDevice, planeIndex, pDisplayCount, ffi.NULL)
		_raiseException(ret)
		pDisplays = ffi.new('struct VkDisplayKHR_T *[]', pDisplayCount[0])
		ret = _callApi(fn, physicalDevice, planeIndex, pDisplayCount, pDisplays, )
		_raiseException(ret)
		return pDisplays		
	return vkGetDisplayPlaneSupportedDisplaysKHR

def vkGetDisplayModePropertiesKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetDisplayModePropertiesKHR', fn)
	def vkGetDisplayModePropertiesKHR(physicalDevice, display, ):
		pPropertyCount = ffi.new('unsigned int *')
		ret = _callApi(fn, physicalDevice, display, pPropertyCount, ffi.NULL)
		_raiseException(ret)
		pProperties = ffi.new('VkDisplayModePropertiesKHR[]', pPropertyCount[0])
		ret = _callApi(fn, physicalDevice, display, pPropertyCount, pProperties, )
		_raiseException(ret)
		return pProperties		
	return vkGetDisplayModePropertiesKHR

def vkCreateDisplayModeKHRWrapper(fn):
	fn = ffi.cast('PFN_vkCreateDisplayModeKHR', fn)
	def vkCreateDisplayModeKHR(physicalDevice, display, pCreateInfo, pAllocator, ):
		pMode = ffi.new('struct VkDisplayModeKHR_T * *')
		ret = _callApi(fn, physicalDevice, display, pCreateInfo, pAllocator, pMode, )
		_raiseException(ret)
		return pMode[0]		
	return vkCreateDisplayModeKHR

def vkGetDisplayPlaneCapabilitiesKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetDisplayPlaneCapabilitiesKHR', fn)
	def vkGetDisplayPlaneCapabilitiesKHR(physicalDevice, mode, planeIndex, ):
		pCapabilities = ffi.new('VkDisplayPlaneCapabilitiesKHR *')
		ret = _callApi(fn, physicalDevice, mode, planeIndex, pCapabilities, )
		_raiseException(ret)
		return pCapabilities[0]		
	return vkGetDisplayPlaneCapabilitiesKHR

def vkCreateDisplayPlaneSurfaceKHRWrapper(fn):
	fn = ffi.cast('PFN_vkCreateDisplayPlaneSurfaceKHR', fn)
	def vkCreateDisplayPlaneSurfaceKHR(instance, pCreateInfo, pAllocator, ):
		pSurface = ffi.new('struct VkSurfaceKHR_T * *')
		ret = _callApi(fn, instance, pCreateInfo, pAllocator, pSurface, )
		_raiseException(ret)
		return pSurface[0]		
	return vkCreateDisplayPlaneSurfaceKHR

def vkCreateSharedSwapchainsKHRWrapper(fn):
	fn = ffi.cast('PFN_vkCreateSharedSwapchainsKHR', fn)
	def vkCreateSharedSwapchainsKHR(device, swapchainCount, pCreateInfos, pAllocator, pSwapchains, ):
		ret = _callApi(fn, device, swapchainCount, pCreateInfos, pAllocator, pSwapchains, )
		_raiseException(ret)
	return vkCreateSharedSwapchainsKHR

def vkCreateDebugReportCallbackEXTWrapper(fn):
	fn = ffi.cast('PFN_vkCreateDebugReportCallbackEXT', fn)
	def vkCreateDebugReportCallbackEXT(instance, pCreateInfo, pAllocator, ):
		pCallback = ffi.new('struct VkDebugReportCallbackEXT_T * *')
		ret = _callApi(fn, instance, pCreateInfo, pAllocator, pCallback, )
		_raiseException(ret)
		return pCallback[0]		
	return vkCreateDebugReportCallbackEXT

def vkDestroyDebugReportCallbackEXTWrapper(fn):
	fn = ffi.cast('PFN_vkDestroyDebugReportCallbackEXT', fn)
	def vkDestroyDebugReportCallbackEXT(instance, callback, pAllocator, ):
		ret = _callApi(fn, instance, callback, pAllocator, )
	return vkDestroyDebugReportCallbackEXT

def vkDebugReportMessageEXTWrapper(fn):
	fn = ffi.cast('PFN_vkDebugReportMessageEXT', fn)
	def vkDebugReportMessageEXT(instance, flags, objectType, object, location, messageCode, pLayerPrefix, pMessage, ):
		ret = _callApi(fn, instance, flags, objectType, object, location, messageCode, pLayerPrefix, pMessage, )
	return vkDebugReportMessageEXT

def vkCreateXlibSurfaceKHRWrapper(fn):
	fn = ffi.cast('PFN_vkCreateXlibSurfaceKHR', fn)
	def vkCreateXlibSurfaceKHR(instance, pCreateInfo, pAllocator, ):
		pSurface = ffi.new('struct VkSurfaceKHR_T * *')
		ret = _callApi(fn, instance, pCreateInfo, pAllocator, pSurface, )
		_raiseException(ret)
		return pSurface[0]		
	return vkCreateXlibSurfaceKHR

def vkGetPhysicalDeviceXlibPresentationSupportKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceXlibPresentationSupportKHR', fn)
	def vkGetPhysicalDeviceXlibPresentationSupportKHR(physicalDevice, queueFamilyIndex, dpy, visualID, ):
		ret = _callApi(fn, physicalDevice, queueFamilyIndex, dpy, visualID, )
		return ret		
	return vkGetPhysicalDeviceXlibPresentationSupportKHR

def vkCreateXcbSurfaceKHRWrapper(fn):
	fn = ffi.cast('PFN_vkCreateXcbSurfaceKHR', fn)
	def vkCreateXcbSurfaceKHR(instance, pCreateInfo, pAllocator, ):
		pSurface = ffi.new('struct VkSurfaceKHR_T * *')
		ret = _callApi(fn, instance, pCreateInfo, pAllocator, pSurface, )
		_raiseException(ret)
		return pSurface[0]		
	return vkCreateXcbSurfaceKHR

def vkGetPhysicalDeviceXcbPresentationSupportKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceXcbPresentationSupportKHR', fn)
	def vkGetPhysicalDeviceXcbPresentationSupportKHR(physicalDevice, queueFamilyIndex, connection, visual_id, ):
		ret = _callApi(fn, physicalDevice, queueFamilyIndex, connection, visual_id, )
		return ret		
	return vkGetPhysicalDeviceXcbPresentationSupportKHR

def vkCreateWaylandSurfaceKHRWrapper(fn):
	fn = ffi.cast('PFN_vkCreateWaylandSurfaceKHR', fn)
	def vkCreateWaylandSurfaceKHR(instance, pCreateInfo, pAllocator, pSurface, ):
		ret = _callApi(fn, instance, pCreateInfo, pAllocator, pSurface, )
		_raiseException(ret)
	return vkCreateWaylandSurfaceKHR

def vkGetPhysicalDeviceWaylandPresentationSupportKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceWaylandPresentationSupportKHR', fn)
	def vkGetPhysicalDeviceWaylandPresentationSupportKHR(physicalDevice, queueFamilyIndex, display, ):
		ret = _callApi(fn, physicalDevice, queueFamilyIndex, display, )
		return ret		
	return vkGetPhysicalDeviceWaylandPresentationSupportKHR

def vkCreateMirSurfaceKHRWrapper(fn):
	fn = ffi.cast('PFN_vkCreateMirSurfaceKHR', fn)
	def vkCreateMirSurfaceKHR(instance, pCreateInfo, pAllocator, pSurface, ):
		ret = _callApi(fn, instance, pCreateInfo, pAllocator, pSurface, )
		_raiseException(ret)
	return vkCreateMirSurfaceKHR

def vkGetPhysicalDeviceMirPresentationSupportKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceMirPresentationSupportKHR', fn)
	def vkGetPhysicalDeviceMirPresentationSupportKHR(physicalDevice, queueFamilyIndex, connection, ):
		ret = _callApi(fn, physicalDevice, queueFamilyIndex, connection, )
		return ret		
	return vkGetPhysicalDeviceMirPresentationSupportKHR

def vkCreateAndroidSurfaceKHRWrapper(fn):
	fn = ffi.cast('PFN_vkCreateAndroidSurfaceKHR', fn)
	def vkCreateAndroidSurfaceKHR(instance, pCreateInfo, pAllocator, pSurface, ):
		ret = _callApi(fn, instance, pCreateInfo, pAllocator, pSurface, )
		_raiseException(ret)
	return vkCreateAndroidSurfaceKHR

def vkCreateWin32SurfaceKHRWrapper(fn):
	fn = ffi.cast('PFN_vkCreateWin32SurfaceKHR', fn)
	def vkCreateWin32SurfaceKHR(instance, pCreateInfo, pAllocator, pSurface, ):
		ret = _callApi(fn, instance, pCreateInfo, pAllocator, pSurface, )
		_raiseException(ret)
	return vkCreateWin32SurfaceKHR

def vkGetPhysicalDeviceWin32PresentationSupportKHRWrapper(fn):
	fn = ffi.cast('PFN_vkGetPhysicalDeviceWin32PresentationSupportKHR', fn)
	def vkGetPhysicalDeviceWin32PresentationSupportKHR(physicalDevice, queueFamilyIndex, ):
		ret = _callApi(fn, physicalDevice, queueFamilyIndex, )
		return ret		
	return vkGetPhysicalDeviceWin32PresentationSupportKHR


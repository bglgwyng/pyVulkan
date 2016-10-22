from pyVulkan import *
import sdl2
import ctypes
import sys


def string(char_ptr):
    if sys.version_info < (3, 0):
        return ffi.string(char_ptr)
    else:
        return ffi.string(char_ptr).decode('ascii')


class Demo:
    def __init__(self):

        app_name = 'Demo'

        self.width = 300
        self.height = 300

        self.setup_cmd = VK_NULL_HANDLE
        self.old_swapchain = VK_NULL_HANDLE
        depth_stencil = 1.0
        #initialize
        app_info = VkApplicationInfo(pApplicationName=app_name,
                                    applicationVersion=0,
                                    pEngineName=app_name,
                                    engineVersion=0,
                                    apiVersion=VK_MAKE_VERSION(1, 0, 0))

        def _getInstanceLayers():
            instance_validation_layers_alts = [["VK_LAYER_LUNARG_standard_validation"],
                                            ["VK_LAYER_GOOGLE_threading", "VK_LAYER_LUNARG_parameter_validation",
                                            "VK_LAYER_LUNARG_device_limits", "VK_LAYER_LUNARG_object_tracker",
                                            "VK_LAYER_LUNARG_image", "VK_LAYER_LUNARG_core_validation",
                                            "VK_LAYER_LUNARG_swapchain", "VK_LAYER_GOOGLE_unique_objects"]]

            instance_layer_names = [string(i.layerName) for _, i in enumerate(vkEnumerateInstanceLayerProperties())]
            return next((i for i in instance_validation_layers_alts if set(i).issubset(instance_layer_names)), [])

        # instance_layers = []
        instance_layers = _getInstanceLayers()

        extensions = [string(i.extensionName) for i in vkEnumerateInstanceExtensionProperties(None)]

        @vkDebugReportCallbackEXT
        def dbgFunc(*args):
            print (string(args[6]))
            return True

        debug_info = VkDebugReportCallbackCreateInfoEXT(pfnCallback=dbgFunc,
                                                        flags=VK_DEBUG_REPORT_ERROR_BIT_EXT | VK_DEBUG_REPORT_WARNING_BIT_EXT)

        instance_info = VkInstanceCreateInfo(pApplicationInfo=app_info,
                                            enabledLayerCount=len(instance_layers),
                                            ppEnabledLayerNames=instance_layers,
                                            enabledExtensionCount=len(extensions),
                                            ppEnabledExtensionNames=extensions,
                                            pNext=debug_info)

        ptrs = set()

        @vkAllocationFunction
        def allocFunc(*args):
            temp = ffi.new("char[]", args[1])
            ptrs.add(temp)
            return temp

        @vkFreeFunction
        def freeFunc(*args):
            if args[1] != ffi.NULL:
                ptrs.remove(args[1])

        @vkReallocationFunction
        def reallocFunc(*args):
            raise NotImplementedError()

        @vkInternalAllocationNotification
        def internalAllocNotify(*args):
            raise NotImplementedError()

        @vkInternalFreeNotification
        def internalFreeNotify(*args):
            raise NotImplementedError()

        allocation_callbacks = VkAllocationCallbacks(pUserData=None,
                                                    pfnAllocation=allocFunc,
                                                    pfnReallocation=reallocFunc,
                                                    pfnFree=freeFunc,
                                                    pfnInternalAllocation=internalAllocNotify,
                                                    pfnInternalFree=internalFreeNotify)

        # inst = vkCreateInstance(instance_info, allocation_callbacks)
        self.inst = vkCreateInstance(instance_info, None)

        self.vkDestroySurfaceKHR = vkGetInstanceProcAddr(self.inst, 'vkDestroySurfaceKHR')
        vkGetPhysicalDeviceSurfaceSupportKHR = vkGetInstanceProcAddr(self.inst, 'vkGetPhysicalDeviceSurfaceSupportKHR')
        vkGetPhysicalDeviceSurfaceFormatsKHR = vkGetInstanceProcAddr(self.inst, 'vkGetPhysicalDeviceSurfaceFormatsKHR')
        vkGetPhysicalDeviceSurfaceCapabilitiesKHR = vkGetInstanceProcAddr(self.inst, 'vkGetPhysicalDeviceSurfaceCapabilitiesKHR')
        vkGetPhysicalDeviceSurfacePresentModesKHR = vkGetInstanceProcAddr(self.inst, 'vkGetPhysicalDeviceSurfacePresentModesKHR')

        vkCreateDebugReportCallbackEXT = vkGetInstanceProcAddr(self.inst, 'vkCreateDebugReportCallbackEXT')
        self.vkDestroyDebugReportCallbackEXT = vkGetInstanceProcAddr(self.inst, 'vkDestroyDebugReportCallbackEXT')

        self.debug_callback = vkCreateDebugReportCallbackEXT(self.inst, debug_info, None)

        gpu = vkEnumeratePhysicalDevices(self.inst)[0]

        gpu_props = vkGetPhysicalDeviceProperties(gpu)
        queue_props = vkGetPhysicalDeviceQueueFamilyProperties(gpu)

        features = vkGetPhysicalDeviceFeatures(gpu)

        ##init sdl
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            print(sdl2.SDL_GetError())

        self.window = sdl2.SDL_CreateWindow(app_name.encode('ascii'), sdl2.SDL_WINDOWPOS_UNDEFINED, sdl2.SDL_WINDOWPOS_UNDEFINED, self.width, self.height, 0)

        if not self.window:
            print(sdl2.SDL_GetError())

        wm_info = sdl2.SDL_SysWMinfo()

        sdl2.SDL_VERSION(wm_info.version)
        sdl2.SDL_GetWindowWMInfo(self.window, ctypes.byref(wm_info))
        if wm_info.subsystem == sdl2.SDL_SYSWM_X11:
            vkCreateXlibSurfaceKHR = vkGetInstanceProcAddr(self.inst, 'vkCreateXlibSurfaceKHR')
            self.surface = vkCreateXlibSurfaceKHR(self.inst, VkXlibSurfaceCreateInfoKHR(dpy=wm_info.info.x11.display, window=wm_info.info.x11.window), None)
        elif wm_info.subsystem == sdl2.SDL_SYSWM_WINDOWS:
            vkCreateWin32SurfaceKHR = vkGetInstanceProcAddr(self.inst, 'vkCreateWin32SurfaceKHR')
            import win32misc
            hinstance = win32misc.getInstance(wm_info.info.win.window)
            self.surface = vkCreateWin32SurfaceKHR(self.inst, VkWin32SurfaceCreateInfoKHR(hinstance=hinstance, hwnd=wm_info.info.win.window), None)
        else:
            assert False

        support_presents = [vkGetPhysicalDeviceSurfaceSupportKHR(gpu, i, self.surface) for i, _ in enumerate(queue_props)]

        graphics_queue_node_index = None
        present_queue_node_index = None

        for i, v in enumerate(queue_props):
            if v.queueFlags & VK_QUEUE_GRAPHICS_BIT:
                if not graphics_queue_node_index:
                    graphics_queue_node_index = i

                if support_presents[i] == VK_TRUE:
                    graphics_queue_node_index = i
                    present_queue_node_index = i
                    break

        if not present_queue_node_index:
            for i, v in enumerate(support_presents):
                if v == VK_TRUE:
                    present_queue_node_index = i

        assert (graphics_queue_node_index is not None) and (present_queue_node_index is not None)
        assert graphics_queue_node_index == present_queue_node_index
        queue_info = VkDeviceQueueCreateInfo(queueFamilyIndex=graphics_queue_node_index,
                                            queueCount=1,
                                            pQueuePriorities=[0.0])

        extensions = [string(i.extensionName) for i in vkEnumerateDeviceExtensionProperties(gpu, None)]

        device_info = VkDeviceCreateInfo(queueCreateInfoCount=1,
                                        pQueueCreateInfos=queue_info,
                                        pEnabledFeatures=VkPhysicalDeviceFeatures(),
                                        ppEnabledLayerNames=[],
                                        ppEnabledExtensionNames=extensions)

        self.device = vkCreateDevice(gpu, device_info, None)

        vkCreateSwapchainKHR = vkGetDeviceProcAddr(self.device, 'vkCreateSwapchainKHR')
        vkGetSwapchainImagesKHR = vkGetDeviceProcAddr(self.device, 'vkGetSwapchainImagesKHR')
        self.vkAcquireNextImageKHR = vkGetDeviceProcAddr(self.device, 'vkAcquireNextImageKHR')
        self.vkQueuePresentKHR = vkGetDeviceProcAddr(self.device, 'vkQueuePresentKHR')
        self.vkDestroySwapchainKHR = vkGetDeviceProcAddr(self.device, 'vkDestroySwapchainKHR')

        self.queue = vkGetDeviceQueue(self.device, graphics_queue_node_index, 0)

        surface_formats = vkGetPhysicalDeviceSurfaceFormatsKHR(gpu, self.surface)

        if len(surface_formats) == 1 and surface_formats[0].format == VK_FORMAT_UNDEFINED:
            format_ = VK_FORMAT_B8G8R8A8_UNORM
        else:
            format_ = surface_formats[0].format
        color_space = surface_formats[0].colorSpace

        self.memory_properties = vkGetPhysicalDeviceMemoryProperties(gpu)

        self.cmd_pool_info = VkCommandPoolCreateInfo(queueFamilyIndex=graphics_queue_node_index, flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT)

        self.cmd_pool = vkCreateCommandPool(self.device, self.cmd_pool_info, None)

        cmd_buffer_info = VkCommandBufferAllocateInfo(commandPool=self.cmd_pool,
                                                    level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
                                                    commandBufferCount=1)

        self.draw_cmd = vkAllocateCommandBuffers(self.device, cmd_buffer_info)[0]

        surface_capabilities = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(gpu, self.surface)

        present_modes = vkGetPhysicalDeviceSurfacePresentModesKHR(gpu, self.surface)

        if surface_capabilities.currentExtent.width == ffi.cast('uint32_t', -1):
            swapchain_extent = VkExtent2D(width=self.width, height=height)
        else:
            swapchain_extent = surface_capabilities.currentExtent
            width = surface_capabilities.currentExtent.width
            height = surface_capabilities.currentExtent.height

        swapchain_present_mode = VK_PRESENT_MODE_MAILBOX_KHR

        desiredNumberOfSwapchainImages = surface_capabilities.minImageCount + 1
        if (surface_capabilities.maxImageCount > 0) and (desiredNumberOfSwapchainImages > surface_capabilities.maxImageCount):
            desiredNumberOfSwapchainImages = surface_capabilities.maxImageCount

        pre_transform = VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR if surface_capabilities.supportedTransforms & VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR else surface_capabilities.currentTransform

        swapchain_info = VkSwapchainCreateInfoKHR(surface=self.surface,
                                                minImageCount=desiredNumberOfSwapchainImages,
                                                imageFormat=format_,
                                                imageColorSpace=color_space,
                                                imageExtent=swapchain_extent,
                                                imageUsage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
                                                preTransform=pre_transform,
                                                compositeAlpha=VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
                                                imageArrayLayers=1,
                                                imageSharingMode=VK_SHARING_MODE_EXCLUSIVE,
                                                presentMode=swapchain_present_mode,
                                                oldSwapchain=self.old_swapchain,
                                                clipped=True)

        self.swapchain = vkCreateSwapchainKHR(self.device, swapchain_info, None)

        self.swapchain_images = vkGetSwapchainImagesKHR(self.device, self.swapchain)

        def _getView(image):
            self.set_image_layout(image, VK_IMAGE_ASPECT_COLOR_BIT, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR, 0, VK_ACCESS_MEMORY_READ_BIT)
            return vkCreateImageView(self.device, VkImageViewCreateInfo(format=format_,
                                                                components={'r': VK_COMPONENT_SWIZZLE_R,
                                                                            'g': VK_COMPONENT_SWIZZLE_G,
                                                                            'b': VK_COMPONENT_SWIZZLE_B,
                                                                            'a': VK_COMPONENT_SWIZZLE_A},
                                                                subresourceRange={'aspectMask': VK_IMAGE_ASPECT_COLOR_BIT,
                                                                                    'baseMipLevel': 0,
                                                                                    'levelCount': 1,
                                                                                    'baseArrayLayer': 0,
                                                                                    'layerCount': 1},
                                                                viewType=VK_IMAGE_VIEW_TYPE_2D,
                                                                flags=0,
                                                                image=image), None)

        self.views = [_getView(i) for i in self.swapchain_images]

        current_buffer = 0

        depth_format = VK_FORMAT_D16_UNORM
        image = VkImageCreateInfo(imageType=VK_IMAGE_TYPE_2D,
                                format=depth_format,
                                extent=[self.width, self.height, 1],
                                mipLevels=1,
                                arrayLayers=1,
                                samples=VK_SAMPLE_COUNT_1_BIT,
                                tiling=VK_IMAGE_TILING_OPTIMAL,
                                usage=VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT)

        mem_alloc = VkMemoryAllocateInfo()

        view = VkImageViewCreateInfo(format=depth_format,
                                    subresourceRange=VkImageSubresourceRange(aspectMask=VK_IMAGE_ASPECT_DEPTH_BIT,
                                                                            baseMipLevel=0,
                                                                            levelCount=1,
                                                                            baseArrayLayer=0,
                                                                            layerCount=1),
                                    viewType=VK_IMAGE_VIEW_TYPE_2D)

        self.depth_image = vkCreateImage(self.device, image, None)

        mem_reqs = vkGetImageMemoryRequirements(self.device, self.depth_image)

        mem_alloc.allocationSize = mem_reqs.size
        mem_alloc.memoryTypeIndex = self.memory_type_from_properties(mem_reqs.memoryTypeBits, 0)

        self.depth_mem = vkAllocateMemory(self.device, mem_alloc, None)

        vkBindImageMemory(self.device, self.depth_image, self.depth_mem, 0)

        self.set_image_layout(self.depth_image, VK_IMAGE_ASPECT_DEPTH_BIT,
                              VK_IMAGE_LAYOUT_UNDEFINED,
                              VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
                              0)

        view.image = self.depth_image

        self.depth_view = vkCreateImageView(self.device, view, None)

        attachments = [VkAttachmentDescription(format=format_,
                                            samples=VK_SAMPLE_COUNT_1_BIT,
                                            loadOp=VK_ATTACHMENT_LOAD_OP_CLEAR,
                                            storeOp=VK_ATTACHMENT_STORE_OP_STORE,
                                            stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE,
                                            stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE,
                                            initialLayout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                                            finalLayout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL),
                    VkAttachmentDescription(format=depth_format,
                                         samples=VK_SAMPLE_COUNT_1_BIT,
                                         loadOp=VK_ATTACHMENT_LOAD_OP_CLEAR,
                                         storeOp=VK_ATTACHMENT_STORE_OP_DONT_CARE,
                                         stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE,
                                         stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE,
                                         initialLayout=VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
                                         finalLayout=VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL)]

        color_reference = VkAttachmentReference(attachment=0, layout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)
        depth_reference = VkAttachmentReference(attachment=1, layout=VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL)

        subpass = VkSubpassDescription(pipelineBindPoint=VK_PIPELINE_BIND_POINT_GRAPHICS,
                                        colorAttachmentCount=1,
                                        pColorAttachments=[color_reference],
                                        pDepthStencilAttachment=depth_reference)

        rp_info = VkRenderPassCreateInfo(attachmentCount=len(attachments),
                                        pAttachments=attachments,
                                        subpassCount=1,
                                        pSubpasses=[subpass])

        self.render_pass = vkCreateRenderPass(self.device, rp_info, None)

        self.framebuffers = [vkCreateFramebuffer(self.device, VkFramebufferCreateInfo(renderPass=self.render_pass,
                                                                            attachmentCount=2,
                                                                            pAttachments=[v, self.depth_view],
                                                                            width=self.width,
                                                                            height=self.height,
                                                                            layers=1), None) for i, v in enumerate(self.views)]

    def flush_init_cmd(self):
        if self.setup_cmd:
            vkEndCommandBuffer(self.setup_cmd)

            submit_info = VkSubmitInfo(commandBufferCount=1, pCommandBuffers=[self.setup_cmd])

            vkQueueSubmit(self.queue, 1, submit_info, VK_NULL_HANDLE)
            vkQueueWaitIdle(self.queue)

            vkFreeCommandBuffers(self.device, self.cmd_pool, 1, [self.setup_cmd])

            self.setup_cmd = VK_NULL_HANDLE

        cmd_buf_hinfo = VkCommandBufferInheritanceInfo(occlusionQueryEnable=VK_FALSE)
        cmd_buf_info = VkCommandBufferBeginInfo(pInheritanceInfo=cmd_buf_hinfo)

        vkBeginCommandBuffer(self.draw_cmd, cmd_buf_info)
        vkEndCommandBuffer(self.draw_cmd)

    def draw(self):
        vkDeviceWaitIdle(self.device)

        present_complete_semaphore = vkCreateSemaphore(self.device, VkSemaphoreCreateInfo(), None)

        current_buffer = self.vkAcquireNextImageKHR(self.device, self.swapchain, ffi.cast('uint64_t', -1),
                                          present_complete_semaphore,
                                          0)

        self.set_image_layout(self.swapchain_images[current_buffer], VK_IMAGE_ASPECT_COLOR_BIT,
                              VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                              VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_ACCESS_MEMORY_READ_BIT)

        self.flush_init_cmd()

        cmd_buf_hinfo = VkCommandBufferInheritanceInfo(occlusionQueryEnable=VK_FALSE)
        cmd_buf_info = VkCommandBufferBeginInfo(pInheritanceInfo=cmd_buf_hinfo)

        clear_values = [VkClearValue(color={'float32': [0.2, 0.2, 0.2, 0.2]}), VkClearValue(depthStencil={'depth': 1.0, 'stencil': 0})]

        rp_begin = VkRenderPassBeginInfo(renderPass=self.render_pass,
                                        framebuffer=self.framebuffers[current_buffer],
                                        renderArea={'offset': {'x': 0, 'y': 0},
                                                        'extent': {'width': self.width, 'height': self.height}},
                                        clearValueCount=len(clear_values),
                                        pClearValues=clear_values)

        vkBeginCommandBuffer(self.draw_cmd, cmd_buf_info)

        vkCmdBeginRenderPass(self.draw_cmd, rp_begin, VK_SUBPASS_CONTENTS_INLINE)
        vkCmdEndRenderPass(self.draw_cmd)

        pre_present_barrier = VkImageMemoryBarrier(srcAccessMask=VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                                                dstAccessMask=VK_ACCESS_MEMORY_READ_BIT,
                                                oldLayout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                                                newLayout=VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                                                srcQueueFamilyIndex=ffi.cast('uint32_t', VK_QUEUE_FAMILY_IGNORED),
                                                dstQueueFamilyIndex=ffi.cast('uint32_t', VK_QUEUE_FAMILY_IGNORED),
                                                subresourceRange=[VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1],
                                                image=self.swapchain_images[current_buffer])

        vkCmdPipelineBarrier(self.draw_cmd, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                             VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 0, 0, None, 0,
                             None, 1, pre_present_barrier)

        vkEndCommandBuffer(self.draw_cmd)

        submit_info = VkSubmitInfo(waitSemaphoreCount=1,
                                pWaitSemaphores=[present_complete_semaphore],
                                pWaitDstStageMask=[VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT],
                                commandBufferCount=1,
                                pCommandBuffers=[self.draw_cmd])

        vkQueueSubmit(self.queue, 1, [submit_info], VK_NULL_HANDLE)
        vkQueueWaitIdle(self.queue)

        present = VkPresentInfoKHR(swapchainCount=1,
                                pSwapchains=[self.swapchain],
                                pImageIndices=[current_buffer])

        self.vkQueuePresentKHR(self.queue, present)

        vkDestroySemaphore(self.device, present_complete_semaphore, None)

    def run(self):
        #main loop

        running = True
        event = sdl2.SDL_Event()

        last_ticks = 0

        while running:
            while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                if event.type == sdl2.SDL_QUIT:
                    running = False

            new_ticks = sdl2.SDL_GetTicks()
            if new_ticks - last_ticks > 1000 / 30:
                self.draw()
                last_ticks = new_ticks

    def release(self):
        #cleanup

        vkFreeMemory(self.device, self.depth_mem, None)

        for i in self.framebuffers:
            vkDestroyFramebuffer(self.device, i, None)

        if self.setup_cmd:
            vkFreeCommandBuffers(self.device, self.cmd_pool, 1, [self.setup_cmd])
        vkFreeCommandBuffers(self.device, self.cmd_pool, 1, [self.draw_cmd])

        vkDestroyCommandPool(self.device, self.cmd_pool, None)

        vkDestroyRenderPass(self.device, self.render_pass, None)

        for i in self.views:
            vkDestroyImageView(self.device, i, None)

        vkDestroyImageView(self.device, self.depth_view, None)
        vkDestroyImage(self.device, self.depth_image, None)

        self.vkDestroySwapchainKHR(self.device, self.swapchain, None)

        vkDestroyDevice(self.device, None)

        self.vkDestroyDebugReportCallbackEXT(self.inst, self.debug_callback, None)

        self.vkDestroySurfaceKHR(self.inst, self.surface, None)
        vkDestroyInstance(self.inst, None)

        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def memory_type_from_properties(self, typeBits, requirements_mask):
        for i, v in enumerate(self.memory_properties.memoryTypes):
            if (typeBits & 1) == 1:
                if (v.propertyFlags & requirements_mask) == requirements_mask:
                    return i
            typeBits >>= 1
        assert False

    def set_image_layout(self, image, aspect_mask, old_image_layout, new_image_layout, src_access_mask=0, dst_access_mask=0):

        if self.setup_cmd == VK_NULL_HANDLE:
            cmd = VkCommandBufferAllocateInfo(commandPool=self.cmd_pool,
                                                level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
                                                commandBufferCount=1)

            self.setup_cmd = vkAllocateCommandBuffers(self.device, cmd)[0]

            cmd_buf_hinfo = VkCommandBufferInheritanceInfo()
            cmd_buf_info = VkCommandBufferBeginInfo(pInheritanceInfo=cmd_buf_hinfo)

            vkBeginCommandBuffer(self.setup_cmd, cmd_buf_info)

        image_memory_barrier = VkImageMemoryBarrier(srcAccessMask=src_access_mask,
                                                    dstAccessMask=dst_access_mask,
                                                    oldLayout=old_image_layout,
                                                    newLayout=new_image_layout,
                                                    image=image,
                                                    subresourceRange=[aspect_mask, 0, 1, 0, 1])

        dst_stage_masks = {VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL: VK_ACCESS_TRANSFER_READ_BIT,
                        VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL: VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                        VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL: VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
                        VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL: VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_INPUT_ATTACHMENT_READ_BIT}

        if new_image_layout in dst_stage_masks:
            image_memory_barrier.dstAccessMask = dst_stage_masks[new_image_layout]

        src_stages = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
        dest_stages = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT

        vkCmdPipelineBarrier(self.setup_cmd, src_stages, dest_stages, 0, 0, None, 0, None, 1, [image_memory_barrier])

demo = Demo()
demo.run()
demo.release()

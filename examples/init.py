from pyVulkan import *
import sdl2
import ctypes

app_name = 'Initialization demo'

width = 300
height = 300

setup_cmd = VK_NULL_HANDLE
old_swapchain = VK_NULL_HANDLE
depth_stencil = 1.0;

def memory_type_from_properties(typeBits, requirements_mask):
    for i, v in enumerate(memory_properties.memoryTypes):
        if (typeBits&1)==1:
            if (v.propertyFlags&requirements_mask)==requirements_mask:
                return i
        typeBits >>= 1

    assert False

def set_image_layout(image, aspectMask, old_image_layout, new_image_layout, srcAccessMask):

    global setup_cmd

    if setup_cmd==VK_NULL_HANDLE:
        cmd = VkCommandBufferAllocateInfo(commandPool = cmd_pool,
                                            level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
                                            commandBufferCount = 1)
    
        setup_cmd = vkAllocateCommandBuffers(device, cmd)[0];

        cmd_buf_hinfo = VkCommandBufferInheritanceInfo()
        cmd_buf_info = VkCommandBufferBeginInfo(pInheritanceInfo = cmd_buf_hinfo)

        vkBeginCommandBuffer(setup_cmd, cmd_buf_info);


    image_memory_barrier = VkImageMemoryBarrier(srcAccessMask = srcAccessMask,
                                                oldLayout = old_image_layout,
                                                newLayout = new_image_layout,
                                                image = image,
                                                subresourceRange = [aspectMask, 0, 1, 0, 1]);

    dst_stage_masks = {VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL:VK_ACCESS_TRANSFER_READ_BIT,
                    VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL:VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                    VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL:VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
                    VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL:VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_INPUT_ATTACHMENT_READ_BIT}

    if new_image_layout in dst_stage_masks:
        image_memory_barrier.dstAccessMask = dst_stage_masks[new_image_layout]

    
    src_stages = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
    dest_stages = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT

    vkCmdPipelineBarrier(setup_cmd, src_stages, dest_stages, 0, 0, None, 0, None, 1, [image_memory_barrier])

#initialize

app_info = VkApplicationInfo(pApplicationName = app_name,
                            applicationVersion = 0,
                            pEngineName = app_name,
                            engineVersion = 0,
                            apiVersion = VK_MAKE_VERSION(1, 0, 0))

instance_info = VkInstanceCreateInfo(pApplicationInfo = app_info)

inst = vkCreateInstance(instance_info, None)

gpu = vkEnumeratePhysicalDevices(inst)[0]

gpu_props = vkGetPhysicalDeviceProperties(gpu)
queue_props = vkGetPhysicalDeviceQueueFamilyProperties(gpu);

features = vkGetPhysicalDeviceFeatures(gpu)

if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)!=0:
    print(sdl2.SDL_GetError())

window = sdl2.SDL_CreateWindow(app_name, sdl2.SDL_WINDOWPOS_UNDEFINED, sdl2.SDL_WINDOWPOS_UNDEFINED, width, height, 0)

if not window:
    print(sdl2.SDL_GetError())

wm_info = sdl2.SDL_SysWMinfo()

sdl2.SDL_VERSION(wm_info.version)
sdl2.SDL_GetWindowWMInfo(window, ctypes.byref(wm_info))
assert wm_info.subsystem==sdl2.SDL_SYSWM_X11

surface = vkCreateXlibSurfaceKHR(inst, VkXlibSurfaceCreateInfoKHR(dpy = wm_info.info.x11.display, window = wm_info.info.x11.window), None)

support_presents = [vkGetPhysicalDeviceSurfaceSupportKHR(gpu, i, surface) for i, _ in enumerate(queue_props)]

graphics_queue_node_index = None
present_queue_node_index = None

for i, v in enumerate(queue_props):
    if v.queueFlags&VK_QUEUE_GRAPHICS_BIT:
        if not graphics_queue_node_index:
            graphics_queue_node_index = i

        if support_presents[i]==VK_TRUE:
            graphics_queue_node_index = i
            present_queue_node_index = i
            break
    
if not present_queue_node_index:
    for i, v in enumerate(support_presents):
        if v==VK_TRUE:
            present_queue_node_index = i

assert (graphics_queue_node_index is not None) and (present_queue_node_index is not None)
assert graphics_queue_node_index==present_queue_node_index

queue_info = VkDeviceQueueCreateInfo(queueFamilyIndex = graphics_queue_node_index,
                                    queueCount = 1,
                                    pQueuePriorities = [0.0])

device_info = VkDeviceCreateInfo(queueCreateInfoCount = 1,
                                pQueueCreateInfos = queue_info,
                                pEnabledFeatures = VkPhysicalDeviceFeatures(shaderClipDistance = VK_TRUE))

setup_cmd == VK_NULL_HANDLE

device = vkCreateDevice(gpu, device_info, None)

queue = vkGetDeviceQueue(device, graphics_queue_node_index, 0)

surface_formats = vkGetPhysicalDeviceSurfaceFormatsKHR(gpu, surface)

if len(surface_formats)==1 and surface_formats[0].format==VK_FORMAT_UNDEFINED:
    format_ = VK_FORMAT_B8G8R8A8_UNORM;
else:
    format_ = surface_formats[0].format;
color_space = surface_formats[0].colorSpace

memory_properties = vkGetPhysicalDeviceMemoryProperties(gpu);

cmd_pool_info = VkCommandPoolCreateInfo(queueFamilyIndex = graphics_queue_node_index, flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT)

cmd_pool = vkCreateCommandPool(device, cmd_pool_info, None);


cmd_buffer_info = VkCommandBufferAllocateInfo(commandPool = cmd_pool,
                                            level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
                                            commandBufferCount = 1)

draw_cmd = vkAllocateCommandBuffers(device, cmd_buffer_info)[0]


surface_capabilities = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(gpu, surface)

present_modes = vkGetPhysicalDeviceSurfacePresentModesKHR(gpu, surface);

if surface_capabilities.currentExtent.width==ffi.cast('uint32_t', -1):
    swapchain_extent = VkExtent2D(width = width, height = height)
else:
    swapchain_extent = surface_capabilities.currentExtent;
    width = surface_capabilities.currentExtent.width;
    height = surface_capabilities.currentExtent.height;

swapchain_present_mode = VK_PRESENT_MODE_FIFO_KHR;

desiredNumberOfSwapchainImages = surface_capabilities.minImageCount + 1
if ( surface_capabilities.maxImageCount>0 ) and (desiredNumberOfSwapchainImages>surface_capabilities.maxImageCount):
    desiredNumberOfSwapchainImages = surface_capabilities.maxImageCount

if surface_capabilities.supportedTransforms & VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR:
    pre_transform = VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR
else:
    pre_transform = surface_capabilities.currentTransform

swapchain_info = VkSwapchainCreateInfoKHR(surface = surface,
                                        minImageCount = desiredNumberOfSwapchainImages,
                                        imageFormat = format_,
                                        imageColorSpace = color_space,
                                        imageExtent = swapchain_extent,
                                        imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
                                        preTransform = pre_transform,
                                        compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
                                        imageArrayLayers = 1,
                                        imageSharingMode = VK_SHARING_MODE_EXCLUSIVE,
                                        presentMode = swapchain_present_mode,
                                        oldSwapchain = old_swapchain,
                                        clipped = True)

swapchain = vkCreateSwapchainKHR(device, swapchain_info, None)

swapchain_images = vkGetSwapchainImagesKHR(device, swapchain)

views = [vkCreateImageView(device, VkImageViewCreateInfo(format = format_,
                                                        components = {'r':VK_COMPONENT_SWIZZLE_R,
                                                                    'g':VK_COMPONENT_SWIZZLE_G,
                                                                    'b':VK_COMPONENT_SWIZZLE_B,
                                                                    'a':VK_COMPONENT_SWIZZLE_A},
                                                        subresourceRange = {'aspectMask':VK_IMAGE_ASPECT_COLOR_BIT,
                                                                            'baseMipLevel':0,
                                                                            'levelCount':1,
                                                                            'baseArrayLayer':0,
                                                                            'layerCount':1},
                                                        viewType = VK_IMAGE_VIEW_TYPE_2D,
                                                        flags = 0,
                                                        image = i), None) for i in swapchain_images]

current_buffer = 0

depth_format  = VK_FORMAT_D16_UNORM;
image = VkImageCreateInfo(imageType = VK_IMAGE_TYPE_2D,
                        format = depth_format,
                        extent = [width, height, 1],
                        mipLevels = 1,
                        arrayLayers = 1,
                        samples = VK_SAMPLE_COUNT_1_BIT,
                        tiling = VK_IMAGE_TILING_OPTIMAL,
                        usage = VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT)

mem_alloc = VkMemoryAllocateInfo()

view = VkImageViewCreateInfo(format = depth_format,
                            subresourceRange = VkImageSubresourceRange(aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT,
                                                                    baseMipLevel = 0,
                                                                    levelCount = 1,
                                                                    baseArrayLayer = 0,
                                                                    layerCount = 1),
                            viewType = VK_IMAGE_VIEW_TYPE_2D)

depth_image = vkCreateImage(device, image, None)

mem_reqs = vkGetImageMemoryRequirements(device, depth_image)

mem_alloc.allocationSize = mem_reqs.size
mem_alloc.memoryTypeIndex = memory_type_from_properties(mem_reqs.memoryTypeBits, 0)

depth_mem = vkAllocateMemory(device, mem_alloc, None)

vkBindImageMemory(device, depth_image, depth_mem, 0)

set_image_layout(depth_image, VK_IMAGE_ASPECT_DEPTH_BIT,
                      VK_IMAGE_LAYOUT_UNDEFINED,
                      VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
                      0)

view.image = depth_image

depth_view = vkCreateImageView(device, view, None)

attachments = [VkAttachmentDescription(format = format_,
                                    samples = VK_SAMPLE_COUNT_1_BIT,
                                    loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
                                    storeOp = VK_ATTACHMENT_STORE_OP_STORE,
                                    stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
                                    stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
                                    initialLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                                    finalLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)]

color_reference = VkAttachmentReference(attachment = 0, layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)
depth_reference = VkAttachmentReference(attachment = 1, layout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL)
       
subpass = VkSubpassDescription(pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
                                colorAttachmentCount = 1,
                                pColorAttachments = color_reference,
                                pDepthStencilAttachment = depth_reference)

rp_info = VkRenderPassCreateInfo(attachmentCount = len(attachments),
                                pAttachments = attachments,
                                subpassCount = 1,
                                pSubpasses = [subpass])

render_pass = vkCreateRenderPass(device, rp_info, None);

framebuffers = [vkCreateFramebuffer(device, VkFramebufferCreateInfo(renderPass = render_pass,
                                                                    attachmentCount = 2,
                                                                    pAttachments = [v, depth_view],
                                                                    width = width,
                                                                    height = height,
                                                                    layers = 1), None) for i, v in enumerate(views)]

if setup_cmd:
    vkEndCommandBuffer(setup_cmd);

    submit_info = VkSubmitInfo(commandBufferCount = 1, pCommandBuffers = [setup_cmd])

    vkQueueSubmit(queue, 1, submit_info, None);
    vkQueueWaitIdle(queue);

    vkFreeCommandBuffers(device, cmd_pool, 1, [setup_cmd]);

    setup_cmd = VK_NULL_HANDLE

cmd_buf_hinfo = VkCommandBufferInheritanceInfo(occlusionQueryEnable = VK_FALSE)
cmd_buf_info = VkCommandBufferBeginInfo(pInheritanceInfo = cmd_buf_hinfo)

vkBeginCommandBuffer(draw_cmd, cmd_buf_info)
vkEndCommandBuffer(draw_cmd)


def draw():

    global setup_cmd
    global current_buffer

    present_complete_semaphore = vkCreateSemaphore(device, VkSemaphoreCreateInfo(), None);
    
    current_buffer = vkAcquireNextImageKHR(device, swapchain, ffi.cast('uint64_t', -1),
                                      present_complete_semaphore,
                                      None)

    cmd_buf_hinfo = VkCommandBufferInheritanceInfo(occlusionQueryEnable = VK_FALSE)
    cmd_buf_info = VkCommandBufferBeginInfo(pInheritanceInfo = cmd_buf_hinfo)

    clear_values = [VkClearValue(color = {'float32':[0.2, 0.2, 0.2, 0.2]}), VkClearValue(depthStencil = {'depth':1.0, 'stencil':0})]

    rp_begin = VkRenderPassBeginInfo(renderPass = render_pass,
                                    framebuffer = framebuffers[current_buffer],
                                    renderArea = {'offset':{'x':0, 'y':0},
                                                    'extent':{'width':width, 'height':height}},
                                    clearValueCount = len(clear_values),
                                    pClearValues = clear_values)
    
    vkBeginCommandBuffer(draw_cmd, cmd_buf_info);

    vkCmdBeginRenderPass(draw_cmd, rp_begin, VK_SUBPASS_CONTENTS_INLINE)
    vkCmdEndRenderPass(draw_cmd)
    
    vkEndCommandBuffer(draw_cmd);

    submit_info = VkSubmitInfo(waitSemaphoreCount = 1,
                            pWaitSemaphores = [present_complete_semaphore],
                            pWaitDstStageMask = [VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT],
                            commandBufferCount = 1,
                            pCommandBuffers = [draw_cmd])

    
    vkQueueSubmit(queue, 1, [submit_info], None)
    vkQueueWaitIdle(queue)
    
    present = VkPresentInfoKHR(swapchainCount = 1,
                            pSwapchains = [swapchain],
                            pImageIndices = [current_buffer])

    vkQueuePresentKHR(queue, present)

    vkDestroySemaphore(device, present_complete_semaphore, None)

#main loop

running = True
event = sdl2.SDL_Event()

last_ticks = 0

while running:
    while sdl2.SDL_PollEvent(ctypes.byref(event))!=0:
        if event.type == sdl2.SDL_QUIT:
            running = False

    new_ticks = sdl2.SDL_GetTicks()
    if new_ticks-last_ticks>1000/30:
        draw()
        last_ticks = new_ticks

#cleanup

for i in framebuffers:
    vkDestroyFramebuffer(device, i, None);

if setup_cmd:
    vkFreeCommandBuffers(device, cmd_pool, 1, [setup_cmd]);
vkFreeCommandBuffers(device, cmd_pool, 1, [draw_cmd]);

vkDestroyCommandPool(device, cmd_pool, None);

vkDestroyRenderPass(device, render_pass, None);

for i in views:
    vkDestroyImageView(device, i, None)

vkDestroyImageView(device, depth_view, None);
vkDestroyImage(device, depth_image, None);

vkDestroySwapchainKHR(device, swapchain, None);

vkDestroyDevice(device, None);
    
vkDestroySurfaceKHR(inst, surface, None);
vkDestroyInstance(inst, None);

sdl2.SDL_DestroyWindow(window)
sdl2.SDL_Quit()
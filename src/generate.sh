#!/bin/sh
wget https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/1.0/src/vulkan/vk_platform.h -O vk_platform.h
wget https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/1.0/src/vulkan/vulkan.h -O vulkan.h
python cevalheader.py platform.h > ../pyVulkan/_vulkan.h
python generate.py

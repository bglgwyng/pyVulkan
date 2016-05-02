#!/bin/bash
python cevalheader.py platform.h > _vulkan.h
python generate.py
cp _vulkan.h ../pyVulkan/_vulkan.h
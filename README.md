# pyVulkan
Vulkan API bindings for Python

pyVulkan does not provide a raw cffi interface for Vulkan API.  
pyVulkan provides wrapped Vulkan APIs to reduce boilerplate code.  
If you want a raw cffi interface for Vulkan API, use [cevalheader.py](src/cevalheader.py) to generate the code which can be directly passed to ffi.cdef method.

It supports both Python 2 and Python 3.

Tested only on Ubuntu 14.04.

## Installation

```bash
pip install pyVulkan
```

from cffi import FFI
_ffi = FFI()
_ffi.cdef('long __stdcall GetWindowLongA(void* hWnd, int nIndex);')
_lib = _ffi.dlopen('User32.dll')

def getInstance(hWnd):
    return _lib.GetWindowLongA(_ffi.cast('void*', hWnd), -6) #GWL_HINSTANCE

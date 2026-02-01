"""
SDK Loader module for Nutrient Native SDK Python bindings.

This module handles loading the native library and SDK initialization.
"""

import ctypes
import os
import sys
import platform
from pathlib import Path
from typing import Optional
import threading

_sdk_initialized = False
_sdk_lock = threading.Lock()
_native_library: Optional[ctypes.CDLL] = None


class SDKError(Exception):
    """Exception raised for SDK initialization errors."""
    pass


def _get_library_name() -> str:
    system = platform.system().lower()

    if system == "darwin":
        return "libNativeSDK.dylib"
    elif system == "windows":
        return "NativeSDK.dll"
    elif system == "linux":
        return "libNativeSDK.so"
    else:
        raise SDKError(f"Unsupported platform: {system}")


def _get_platform_folder() -> str:
    """Get the platform folder name for native libraries."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        return "macos-universal"
    elif system == "linux":
        if "x86_64" in machine or "amd64" in machine:
            return "linux-amd64"
        elif "aarch64" in machine or "arm64" in machine:
            return "linux-arm64"
    elif system == "windows":
        if "amd64" in machine or "x86_64" in machine:
            return "windows-amd64"
        elif "arm64" in machine:
            return "windows-arm64"

    raise SDKError(f"Unsupported platform: {system} {machine}")


def _find_library() -> Optional[Path]:
    lib_name = _get_library_name()
    platform_folder = _get_platform_folder()

    # Try unified native package (nutrient_sdk_native)
    try:
        import nutrient_sdk_native
        if hasattr(nutrient_sdk_native, 'get_library_file'):
            # get_library_file() sets up NUTRIENT_NATIVE_SDK_PATH environment variable
            lib_file = nutrient_sdk_native.get_library_file()
            if lib_file and Path(lib_file).exists():
                return Path(lib_file)
    except (ImportError, FileNotFoundError) as e:
        pass

    search_paths = [
        Path(__file__).parent / "lib" / platform_folder / lib_name,
        Path(__file__).parent / "lib" / lib_name,
        Path(__file__).parent.parent / "lib" / platform_folder / lib_name,
        Path(__file__).parent.parent / "lib" / lib_name,
        Path(os.environ.get("NUTRIENT_SDK_PATH", "")) / "lib" / platform_folder / lib_name if os.environ.get("NUTRIENT_SDK_PATH") else None,
        Path(os.environ.get("NUTRIENT_SDK_PATH", "")) / "lib" / lib_name if os.environ.get("NUTRIENT_SDK_PATH") else None,
        Path("/usr/local/lib") / lib_name,
        Path("/usr/lib") / lib_name,
        Path("/opt/nutrient/lib") / lib_name,
    ]

    if platform.system() == "Windows":
        search_paths.extend([
            Path(os.environ.get("ProgramFiles", "")) / "Nutrient" / "lib" / lib_name,
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Nutrient" / "lib" / lib_name,
        ])

    for path in search_paths:
        if path and path.exists():
            return path

    return None


def load_native_library() -> ctypes.CDLL:
    """
    Load the native SDK library.
    
    Returns:
        The loaded library handle
        
    Raises:
        SDKError: If the library cannot be loaded
    """
    global _native_library
    
    if _native_library is not None:
        return _native_library
    
    lib_path = _find_library()
    
    if lib_path:
        try:
            _native_library = ctypes.CDLL(str(lib_path))
            return _native_library
        except OSError as e:
            raise SDKError(f"Failed to load native library from {lib_path}: {e}")
    
    lib_name = _get_library_name()
    try:
        _native_library = ctypes.CDLL(lib_name)
        return _native_library
    except OSError as e:
        raise SDKError(
            f"Could not find or load {lib_name}. "
            f"Please ensure the Nutrient SDK is installed and set NUTRIENT_SDK_PATH environment variable. "
            f"Error: {e}"
        )


def initialize_sdk(license_key: Optional[str] = None) -> None:
    """
    Initialize the Nutrient SDK.
    
    Args:
        license_key: Optional license key for SDK activation
        
    Raises:
        SDKError: If initialization fails
    """
    global _sdk_initialized
    
    with _sdk_lock:
        if _sdk_initialized:
            return
        
        lib = load_native_library()
        lib.BridgeLicenseInitializeLicenseInt32String.restype = None
        lib.BridgeLicenseInitializeLicenseInt32String.argtypes = [ctypes.c_int32, ctypes.c_char_p]
        lib.BridgeLicenseInitializeLicenseInt32String(2, "1.0.0".encode('utf-8'))
        lib.BridgeLicenseRegisterKeyString.restype = None
        lib.BridgeLicenseRegisterKeyString.argtypes = [ctypes.c_char_p]

        if license_key:
            lib.BridgeLicenseRegisterKeyString(license_key.encode('utf-8'))
            lib.BridgeLicenseGetLastErrorCode.restype = ctypes.c_int
            lib.BridgeLicenseGetLastErrorCode.argtypes = []
            error_code = lib.BridgeLicenseGetLastErrorCode()
            if error_code != 0:
                raise SDKError(f"SDK initialization failed with code: {error_code}")
        
        _sdk_initialized = True


def shutdown_sdk() -> None:
    """
    Shutdown the Nutrient SDK and release resources.
    """
    global _sdk_initialized, _native_library
    
    with _sdk_lock:
        if not _sdk_initialized:
            return
        
        if _native_library:
            try:
                pass
            except Exception as e:
                pass
            
            _native_library = None
        
        _sdk_initialized = False


def is_sdk_initialized() -> bool:
    """
    Check if the SDK is initialized.
    
    Returns:
        True if the SDK is initialized, False otherwise
    """
    return _sdk_initialized


def get_sdk_version() -> str:
    """
    Get the SDK version string.
    
    Returns:
        The SDK version string
        
    Raises:
        SDKError: If the SDK is not initialized
    """
    if not _sdk_initialized:
        raise SDKError("SDK not initialized. Call initialize_sdk() first.")
    
    if not _native_library:
        raise SDKError("Native library not loaded")

    _native_library.BridgeLicenseGetVersionString.restype = ctypes.c_char_p
    _native_library.BridgeLicenseGetVersionString.argtypes = []
    version_bytes = _native_library.BridgeLicenseGetVersionString()
    if version_bytes:
        return version_bytes.decode('utf-8')

    return "Unknown"


def get_library_handle() -> ctypes.CDLL:
    """
    Get the native library handle for internal use.
    
    Returns:
        The native library handle
        
    Raises:
        SDKError: If the library is not loaded
    """
    if not _native_library:
        raise SDKError("Native library not loaded. Call initialize_sdk() first.")
    
    return _native_library


_string_interop_initialized = False

def _init_string_interop():
    global _string_interop_initialized
    if _string_interop_initialized or _native_library is None:
        return

    _native_library.BridgeStringInteropGetValue.restype = ctypes.c_void_p
    _native_library.BridgeStringInteropGetValue.argtypes = [ctypes.c_void_p]

    _native_library.BridgeStringInteropFreeValue.restype = None
    _native_library.BridgeStringInteropFreeValue.argtypes = [ctypes.c_void_p]

    _string_interop_initialized = True


def convert_string_handle(string_handle) -> Optional[str]:
    """
    Convert a StringInterop GCHandle to a Python string.

    Args:
        string_handle: The GCHandle (IntPtr) returned from the C# bridge

    Returns:
        The string value, or None if the handle was null
    """
    if not string_handle:
        return None

    _init_string_interop()
    string_ptr = _native_library.BridgeStringInteropGetValue(string_handle)
    if not string_ptr:
        return None

    result = ctypes.string_at(string_ptr).decode('utf-8')
    _native_library.BridgeStringInteropFreeValue(string_ptr)

    return result


__all__ = [
    'SDKError',
    'initialize_sdk',
    'shutdown_sdk',
    'is_sdk_initialized',
    'get_sdk_version',
    'load_native_library',
    'get_library_handle',
    'convert_string_handle',
]

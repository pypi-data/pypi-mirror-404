"""
Color module.
"""

import ctypes
import os
import sys
from typing import Optional, Any, Union
from enum import Enum
from pathlib import Path
from importlib import import_module
from . import sdk_helpers
from . import sdk_loader

sdk_loader.initialize_sdk()
_lib = sdk_loader.get_library_handle()


class ColorError(Exception):
    """Exception raised by Color operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeColorInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeColorInitNSDKH.argtypes = []

_lib.BridgeColorCloseNSDKH.restype = None
_lib.BridgeColorCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeColorGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeColorGetLastErrorCode.argtypes = []

_lib.BridgeColorGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeColorGetLastErrorMessage.argtypes = []

_lib.BridgeColorFreeErrorString.restype = None
_lib.BridgeColorFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeColorFromArgbInt32Int32Int32Int32.restype = ctypes.c_void_p
_lib.BridgeColorFromArgbInt32Int32Int32Int32.argtypes = [ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]

_lib.BridgeColorToString.restype = ctypes.c_void_p
_lib.BridgeColorToString.argtypes = [ctypes.c_void_p]


class Color:
    """
    Represents a color in ARGB format.
    """

    def __init__(self):
        """Initialize a new Color instance."""
        self._handle = _lib.BridgeColorInitNSDKH()
        if not self._handle:
            self._check_error()
        self._closed = False

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        """Close and cleanup the native resources."""
        if not self._closed and self._handle:
            _lib.BridgeColorCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeColorGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeColorGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeColorFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise ColorError(f"Color: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("Color instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    @classmethod
    def from_argb(cls, alpha: int, red: int, green: int, blue: int) -> 'Color':
        """
        Creates a Color from ARGB components.

        Args:
            alpha (int)
            red (int)
            green (int)
            blue (int)

        Returns:
            'Color': A new Color instance.

        Raises:
            ColorError: If the operation fails
        """

        result = _lib.BridgeColorFromArgbInt32Int32Int32Int32(alpha, red, green, blue)
        error_code = _lib.BridgeColorGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeColorGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeColorFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise ColorError(f"FromArgb: {message} (code: {error_code})")
        return import_module('.color', package=__package__).Color._from_handle(result)

    def to_string(self) -> str:
        """
        Returns a string representation of the color in "A, R, G, B" format.

        Returns:
            str: The result of the operation

        Raises:
            ColorError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeColorToString(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)



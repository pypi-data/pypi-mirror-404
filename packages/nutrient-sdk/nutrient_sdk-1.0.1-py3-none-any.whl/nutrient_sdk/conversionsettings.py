"""
ConversionSettings module.
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


class ConversionSettingsError(Exception):
    """Exception raised by ConversionSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeConversionSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeConversionSettingsGetLastErrorCode.argtypes = []

_lib.BridgeConversionSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeConversionSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeConversionSettingsFreeErrorString.restype = None
_lib.BridgeConversionSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeConversionSettingsGetTimeoutMilliseconds.restype = ctypes.c_int32
_lib.BridgeConversionSettingsGetTimeoutMilliseconds.argtypes = [ctypes.c_void_p]

_lib.BridgeConversionSettingsSetTimeoutMillisecondsInt32.restype = None
_lib.BridgeConversionSettingsSetTimeoutMillisecondsInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class ConversionSettings:
    """
    Merged view of ConversionSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate ConversionSettings directly. Use static factory methods instead."""
        raise TypeError("ConversionSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeConversionSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeConversionSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeConversionSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise ConversionSettingsError(f"ConversionSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("ConversionSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_timeout_milliseconds(self) -> int:
        """
        Gets the TimeoutMilliseconds property.

        Returns:
            int: The value of the TimeoutMilliseconds property.

        Raises:
            ConversionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeConversionSettingsGetTimeoutMilliseconds(self._handle)
        self._check_error()
        return result

    def set_timeout_milliseconds(self, value: int) -> None:
        """
        Sets the TimeoutMilliseconds property.

        Args:
            value (int)

        Returns:
            None: The result of the operation

        Raises:
            ConversionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeConversionSettingsSetTimeoutMillisecondsInt32(self._handle, value)
        self._check_error()

    @property
    def timeout_milliseconds(self) -> int:
        """
        Gets the TimeoutMilliseconds property.

        Returns:
            int: The value of the TimeoutMilliseconds property.
        """
        return self.get_timeout_milliseconds()

    @timeout_milliseconds.setter
    def timeout_milliseconds(self, value: int) -> None:
        """
        Sets the timeout milliseconds.

        Args:
            value (int): The value to set.
        """
        self.set_timeout_milliseconds(value)



"""
JpegSettings module.
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


class JpegSettingsError(Exception):
    """Exception raised by JpegSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeJpegSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeJpegSettingsGetLastErrorCode.argtypes = []

_lib.BridgeJpegSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeJpegSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeJpegSettingsFreeErrorString.restype = None
_lib.BridgeJpegSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeJpegSettingsGetQualitySettings.restype = ctypes.POINTER(ctypes.c_ubyte)
_lib.BridgeJpegSettingsGetQualitySettings.argtypes = [ctypes.c_void_p]

_lib.BridgeJpegSettingsSetQualitySettingsByte.restype = None
_lib.BridgeJpegSettingsSetQualitySettingsByte.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte)]


class JpegSettings:
    """
    Merged view of JpegSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate JpegSettings directly. Use static factory methods instead."""
        raise TypeError("JpegSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeJpegSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeJpegSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeJpegSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise JpegSettingsError(f"JpegSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("JpegSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_quality_settings(self) -> bytes:
        """
        Gets the QualitySettings property.

        Returns:
            bytes: The value of the QualitySettings property.

        Raises:
            JpegSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeJpegSettingsGetQualitySettings(self._handle)
        self._check_error()
        return bytes(ctypes.string_at(result))

    def set_quality_settings(self, value: bytes) -> None:
        """
        Sets the QualitySettings property.

        Args:
            value (bytes)

        Returns:
            None: The result of the operation

        Raises:
            JpegSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeJpegSettingsSetQualitySettingsByte(self._handle, ctypes.cast(value, ctypes.POINTER(ctypes.c_ubyte)))
        self._check_error()

    @property
    def quality_settings(self) -> bytes:
        """
        Gets the QualitySettings property.

        Returns:
            bytes: The value of the QualitySettings property.
        """
        return self.get_quality_settings()

    @quality_settings.setter
    def quality_settings(self, value: bytes) -> None:
        """
        Sets the quality settings.

        Args:
            value (bytes): The value to set.
        """
        self.set_quality_settings(value)



"""
TiffSettings module.
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


class TiffSettingsError(Exception):
    """Exception raised by TiffSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeTiffSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeTiffSettingsGetLastErrorCode.argtypes = []

_lib.BridgeTiffSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeTiffSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeTiffSettingsFreeErrorString.restype = None
_lib.BridgeTiffSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeTiffSettingsGetTiffCompression.restype = ctypes.c_int32
_lib.BridgeTiffSettingsGetTiffCompression.argtypes = [ctypes.c_void_p]

_lib.BridgeTiffSettingsSetTiffCompressionTiffCompression.restype = None
_lib.BridgeTiffSettingsSetTiffCompressionTiffCompression.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class TiffSettings:
    """
    Merged view of TiffSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate TiffSettings directly. Use static factory methods instead."""
        raise TypeError("TiffSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeTiffSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeTiffSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeTiffSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise TiffSettingsError(f"TiffSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("TiffSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_tiff_compression(self) -> Any:
        """
        Gets the TiffCompression property.

        Returns:
            Any: The value of the TiffCompression property.

        Raises:
            TiffSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeTiffSettingsGetTiffCompression(self._handle)
        self._check_error()
        return result

    def set_tiff_compression(self, value: Any) -> None:
        """
        Sets the TiffCompression property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            TiffSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeTiffSettingsSetTiffCompressionTiffCompression(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    @property
    def tiff_compression(self) -> Any:
        """
        Gets the TiffCompression property.

        Returns:
            Any: The value of the TiffCompression property.
        """
        return self.get_tiff_compression()

    @tiff_compression.setter
    def tiff_compression(self, value: Any) -> None:
        """
        Sets the tiff compression.

        Args:
            value (Any): The value to set.
        """
        self.set_tiff_compression(value)



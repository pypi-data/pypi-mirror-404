"""
PdfPageSettings module.
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


class PdfPageSettingsError(Exception):
    """Exception raised by PdfPageSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfPageSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfPageSettingsGetLastErrorCode.argtypes = []

_lib.BridgePdfPageSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfPageSettingsGetLastErrorMessage.argtypes = []

_lib.BridgePdfPageSettingsFreeErrorString.restype = None
_lib.BridgePdfPageSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageSettingsGetPageSize.restype = ctypes.c_int32
_lib.BridgePdfPageSettingsGetPageSize.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageSettingsSetPageSizePdfPageSizes.restype = None
_lib.BridgePdfPageSettingsSetPageSizePdfPageSizes.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class PdfPageSettings:
    """
    Merged view of PdfPageSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate PdfPageSettings directly. Use static factory methods instead."""
        raise TypeError("PdfPageSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfPageSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfPageSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfPageSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfPageSettingsError(f"PdfPageSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfPageSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_page_size(self) -> Any:
        """
        Gets the PageSize property.

        Returns:
            Any: The value of the PageSize property.

        Raises:
            PdfPageSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageSettingsGetPageSize(self._handle)
        self._check_error()
        return result

    def set_page_size(self, value: Any) -> None:
        """
        Sets the PageSize property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            PdfPageSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfPageSettingsSetPageSizePdfPageSizes(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    @property
    def page_size(self) -> Any:
        """
        Gets the PageSize property.

        Returns:
            Any: The value of the PageSize property.
        """
        return self.get_page_size()

    @page_size.setter
    def page_size(self, value: Any) -> None:
        """
        Sets the page size.

        Args:
            value (Any): The value to set.
        """
        self.set_page_size(value)



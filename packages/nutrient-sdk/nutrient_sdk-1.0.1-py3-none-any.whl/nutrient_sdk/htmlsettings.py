"""
HtmlSettings module.
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


class HtmlSettingsError(Exception):
    """Exception raised by HtmlSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeHtmlSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeHtmlSettingsGetLastErrorCode.argtypes = []

_lib.BridgeHtmlSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeHtmlSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeHtmlSettingsFreeErrorString.restype = None
_lib.BridgeHtmlSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeHtmlSettingsGetLayout.restype = ctypes.c_int32
_lib.BridgeHtmlSettingsGetLayout.argtypes = [ctypes.c_void_p]

_lib.BridgeHtmlSettingsSetLayoutHtmlLayoutType.restype = None
_lib.BridgeHtmlSettingsSetLayoutHtmlLayoutType.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class HtmlSettings:
    """
    Merged view of HtmlSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate HtmlSettings directly. Use static factory methods instead."""
        raise TypeError("HtmlSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeHtmlSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeHtmlSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeHtmlSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise HtmlSettingsError(f"HtmlSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("HtmlSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_layout(self) -> Any:
        """
        Gets the Layout property.

        Returns:
            Any: The value of the Layout property.

        Raises:
            HtmlSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeHtmlSettingsGetLayout(self._handle)
        self._check_error()
        return result

    def set_layout(self, value: Any) -> None:
        """
        Sets the Layout property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            HtmlSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeHtmlSettingsSetLayoutHtmlLayoutType(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    @property
    def layout(self) -> Any:
        """
        Gets the Layout property.

        Returns:
            Any: The value of the Layout property.
        """
        return self.get_layout()

    @layout.setter
    def layout(self, value: Any) -> None:
        """
        Sets the layout.

        Args:
            value (Any): The value to set.
        """
        self.set_layout(value)



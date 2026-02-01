"""
DocumentLayoutJsonExportSettings module.
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


class DocumentLayoutJsonExportSettingsError(Exception):
    """Exception raised by DocumentLayoutJsonExportSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeDocumentLayoutJsonExportSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeDocumentLayoutJsonExportSettingsGetLastErrorCode.argtypes = []

_lib.BridgeDocumentLayoutJsonExportSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeDocumentLayoutJsonExportSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeDocumentLayoutJsonExportSettingsFreeErrorString.restype = None
_lib.BridgeDocumentLayoutJsonExportSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentLayoutJsonExportSettingsGetContent.restype = ctypes.c_int32
_lib.BridgeDocumentLayoutJsonExportSettingsGetContent.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentLayoutJsonExportSettingsSetContentJsonExportContent.restype = None
_lib.BridgeDocumentLayoutJsonExportSettingsSetContentJsonExportContent.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeDocumentLayoutJsonExportSettingsGetFormat.restype = ctypes.c_int32
_lib.BridgeDocumentLayoutJsonExportSettingsGetFormat.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentLayoutJsonExportSettingsSetFormatJsonExportFormat.restype = None
_lib.BridgeDocumentLayoutJsonExportSettingsSetFormatJsonExportFormat.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class DocumentLayoutJsonExportSettings:
    """
    Merged view of DocumentLayoutJsonExportSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate DocumentLayoutJsonExportSettings directly. Use static factory methods instead."""
        raise TypeError("DocumentLayoutJsonExportSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeDocumentLayoutJsonExportSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeDocumentLayoutJsonExportSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeDocumentLayoutJsonExportSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise DocumentLayoutJsonExportSettingsError(f"DocumentLayoutJsonExportSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("DocumentLayoutJsonExportSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_content(self) -> Any:
        """
        Gets the Content property.

        Returns:
            Any: The value of the Content property.

        Raises:
            DocumentLayoutJsonExportSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentLayoutJsonExportSettingsGetContent(self._handle)
        self._check_error()
        return result

    def set_content(self, value: Any) -> None:
        """
        Sets the Content property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            DocumentLayoutJsonExportSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentLayoutJsonExportSettingsSetContentJsonExportContent(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_format(self) -> Any:
        """
        Gets the Format property.

        Returns:
            Any: The value of the Format property.

        Raises:
            DocumentLayoutJsonExportSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentLayoutJsonExportSettingsGetFormat(self._handle)
        self._check_error()
        return result

    def set_format(self, value: Any) -> None:
        """
        Sets the Format property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            DocumentLayoutJsonExportSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentLayoutJsonExportSettingsSetFormatJsonExportFormat(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    @property
    def content(self) -> Any:
        """
        Gets the Content property.

        Returns:
            Any: The value of the Content property.
        """
        return self.get_content()

    @content.setter
    def content(self, value: Any) -> None:
        """
        Sets the content.

        Args:
            value (Any): The value to set.
        """
        self.set_content(value)

    @property
    def format(self) -> Any:
        """
        Gets the Format property.

        Returns:
            Any: The value of the Format property.
        """
        return self.get_format()

    @format.setter
    def format(self, value: Any) -> None:
        """
        Sets the format.

        Args:
            value (Any): The value to set.
        """
        self.set_format(value)



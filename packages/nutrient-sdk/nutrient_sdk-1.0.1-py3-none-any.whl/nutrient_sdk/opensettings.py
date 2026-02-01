"""
OpenSettings module.
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


class OpenSettingsError(Exception):
    """Exception raised by OpenSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeOpenSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeOpenSettingsGetLastErrorCode.argtypes = []

_lib.BridgeOpenSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeOpenSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeOpenSettingsFreeErrorString.restype = None
_lib.BridgeOpenSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenSettingsGetPageCacheMode.restype = ctypes.c_int32
_lib.BridgeOpenSettingsGetPageCacheMode.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenSettingsSetPageCacheModePageCacheMode.restype = None
_lib.BridgeOpenSettingsSetPageCacheModePageCacheMode.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeOpenSettingsGetMode.restype = ctypes.c_int32
_lib.BridgeOpenSettingsGetMode.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenSettingsSetModeOpenSettingsMode.restype = None
_lib.BridgeOpenSettingsSetModeOpenSettingsMode.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeOpenSettingsGetDocumentFormat.restype = ctypes.c_int32
_lib.BridgeOpenSettingsGetDocumentFormat.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenSettingsSetDocumentFormatDocumentFormat.restype = None
_lib.BridgeOpenSettingsSetDocumentFormatDocumentFormat.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeOpenSettingsGetMaxPages.restype = ctypes.c_int32
_lib.BridgeOpenSettingsGetMaxPages.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenSettingsSetMaxPagesInt32.restype = None
_lib.BridgeOpenSettingsSetMaxPagesInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeOpenSettingsGetImplicitConversion.restype = ctypes.c_int32
_lib.BridgeOpenSettingsGetImplicitConversion.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenSettingsSetImplicitConversionImplicitConversion.restype = None
_lib.BridgeOpenSettingsSetImplicitConversionImplicitConversion.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class OpenSettings:
    """
    Merged view of OpenSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate OpenSettings directly. Use static factory methods instead."""
        raise TypeError("OpenSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeOpenSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeOpenSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeOpenSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise OpenSettingsError(f"OpenSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("OpenSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_page_cache_mode(self) -> Any:
        """
        Gets the PageCacheMode property.

        Returns:
            Any: The value of the PageCacheMode property.

        Raises:
            OpenSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenSettingsGetPageCacheMode(self._handle)
        self._check_error()
        return result

    def set_page_cache_mode(self, value: Any) -> None:
        """
        Sets the PageCacheMode property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            OpenSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenSettingsSetPageCacheModePageCacheMode(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_mode(self) -> Any:
        """
        Gets the Mode property.

        Returns:
            Any: The value of the Mode property.

        Raises:
            OpenSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenSettingsGetMode(self._handle)
        self._check_error()
        return result

    def set_mode(self, value: Any) -> None:
        """
        Sets the Mode property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            OpenSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenSettingsSetModeOpenSettingsMode(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_document_format(self) -> Any:
        """
        Gets the DocumentFormat property.

        Returns:
            Any: The value of the DocumentFormat property.

        Raises:
            OpenSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenSettingsGetDocumentFormat(self._handle)
        self._check_error()
        return result

    def set_document_format(self, value: Any) -> None:
        """
        Sets the DocumentFormat property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            OpenSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenSettingsSetDocumentFormatDocumentFormat(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_max_pages(self) -> int:
        """
        Gets the MaxPages property.

        Returns:
            int: The value of the MaxPages property.

        Raises:
            OpenSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenSettingsGetMaxPages(self._handle)
        self._check_error()
        return result

    def set_max_pages(self, value: int) -> None:
        """
        Sets the MaxPages property.

        Args:
            value (int)

        Returns:
            None: The result of the operation

        Raises:
            OpenSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenSettingsSetMaxPagesInt32(self._handle, value)
        self._check_error()

    def get_implicit_conversion(self) -> Any:
        """
        Gets the ImplicitConversion property.

        Returns:
            Any: The value of the ImplicitConversion property.

        Raises:
            OpenSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenSettingsGetImplicitConversion(self._handle)
        self._check_error()
        return result

    def set_implicit_conversion(self, value: Any) -> None:
        """
        Sets the ImplicitConversion property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            OpenSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenSettingsSetImplicitConversionImplicitConversion(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    @property
    def page_cache_mode(self) -> Any:
        """
        Gets the PageCacheMode property.

        Returns:
            Any: The value of the PageCacheMode property.
        """
        return self.get_page_cache_mode()

    @page_cache_mode.setter
    def page_cache_mode(self, value: Any) -> None:
        """
        Sets the page cache mode.

        Args:
            value (Any): The value to set.
        """
        self.set_page_cache_mode(value)

    @property
    def mode(self) -> Any:
        """
        Gets the Mode property.

        Returns:
            Any: The value of the Mode property.
        """
        return self.get_mode()

    @mode.setter
    def mode(self, value: Any) -> None:
        """
        Sets the mode.

        Args:
            value (Any): The value to set.
        """
        self.set_mode(value)

    @property
    def document_format(self) -> Any:
        """
        Gets the DocumentFormat property.

        Returns:
            Any: The value of the DocumentFormat property.
        """
        return self.get_document_format()

    @document_format.setter
    def document_format(self, value: Any) -> None:
        """
        Sets the document format.

        Args:
            value (Any): The value to set.
        """
        self.set_document_format(value)

    @property
    def max_pages(self) -> int:
        """
        Gets the MaxPages property.

        Returns:
            int: The value of the MaxPages property.
        """
        return self.get_max_pages()

    @max_pages.setter
    def max_pages(self, value: int) -> None:
        """
        Sets the max pages.

        Args:
            value (int): The value to set.
        """
        self.set_max_pages(value)

    @property
    def implicit_conversion(self) -> Any:
        """
        Gets the ImplicitConversion property.

        Returns:
            Any: The value of the ImplicitConversion property.
        """
        return self.get_implicit_conversion()

    @implicit_conversion.setter
    def implicit_conversion(self, value: Any) -> None:
        """
        Sets the implicit conversion.

        Args:
            value (Any): The value to set.
        """
        self.set_implicit_conversion(value)



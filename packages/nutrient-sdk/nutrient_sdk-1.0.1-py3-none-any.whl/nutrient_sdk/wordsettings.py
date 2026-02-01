"""
WordSettings module.
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


class WordSettingsError(Exception):
    """Exception raised by WordSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeWordSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeWordSettingsGetLastErrorCode.argtypes = []

_lib.BridgeWordSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeWordSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeWordSettingsFreeErrorString.restype = None
_lib.BridgeWordSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeWordSettingsGetMarkupMode.restype = ctypes.c_int32
_lib.BridgeWordSettingsGetMarkupMode.argtypes = [ctypes.c_void_p]

_lib.BridgeWordSettingsSetMarkupModeDocumentMarkupMode.restype = None
_lib.BridgeWordSettingsSetMarkupModeDocumentMarkupMode.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeWordSettingsGetHalfTransparentHeaderFooter.restype = ctypes.c_bool
_lib.BridgeWordSettingsGetHalfTransparentHeaderFooter.argtypes = [ctypes.c_void_p]

_lib.BridgeWordSettingsSetHalfTransparentHeaderFooterBoolean.restype = None
_lib.BridgeWordSettingsSetHalfTransparentHeaderFooterBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]


class WordSettings:
    """
    Merged view of WordSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate WordSettings directly. Use static factory methods instead."""
        raise TypeError("WordSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeWordSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeWordSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeWordSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise WordSettingsError(f"WordSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("WordSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_markup_mode(self) -> Any:
        """
        Gets the MarkupMode property.

        Returns:
            Any: The value of the MarkupMode property.

        Raises:
            WordSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeWordSettingsGetMarkupMode(self._handle)
        self._check_error()
        return result

    def set_markup_mode(self, value: Any) -> None:
        """
        Sets the MarkupMode property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            WordSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeWordSettingsSetMarkupModeDocumentMarkupMode(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_half_transparent_header_footer(self) -> bool:
        """
        Gets the HalfTransparentHeaderFooter property.

        Returns:
            bool: The value of the HalfTransparentHeaderFooter property.

        Raises:
            WordSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeWordSettingsGetHalfTransparentHeaderFooter(self._handle)
        self._check_error()
        return result

    def set_half_transparent_header_footer(self, value: bool) -> None:
        """
        Sets the HalfTransparentHeaderFooter property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            WordSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeWordSettingsSetHalfTransparentHeaderFooterBoolean(self._handle, value)
        self._check_error()

    @property
    def markup_mode(self) -> Any:
        """
        Gets the MarkupMode property.

        Returns:
            Any: The value of the MarkupMode property.
        """
        return self.get_markup_mode()

    @markup_mode.setter
    def markup_mode(self, value: Any) -> None:
        """
        Sets the markup mode.

        Args:
            value (Any): The value to set.
        """
        self.set_markup_mode(value)

    @property
    def half_transparent_header_footer(self) -> bool:
        """
        Gets the HalfTransparentHeaderFooter property.

        Returns:
            bool: The value of the HalfTransparentHeaderFooter property.
        """
        return self.get_half_transparent_header_footer()

    @half_transparent_header_footer.setter
    def half_transparent_header_footer(self, value: bool) -> None:
        """
        Sets the half transparent header footer.

        Args:
            value (bool): The value to set.
        """
        self.set_half_transparent_header_footer(value)



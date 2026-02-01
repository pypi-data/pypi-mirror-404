"""
ReadingOrderSettings module.
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


class ReadingOrderSettingsError(Exception):
    """Exception raised by ReadingOrderSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeReadingOrderSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeReadingOrderSettingsGetLastErrorCode.argtypes = []

_lib.BridgeReadingOrderSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeReadingOrderSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeReadingOrderSettingsFreeErrorString.restype = None
_lib.BridgeReadingOrderSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeReadingOrderSettingsGetHorizontalDilationThreshold.restype = ctypes.c_float
_lib.BridgeReadingOrderSettingsGetHorizontalDilationThreshold.argtypes = [ctypes.c_void_p]

_lib.BridgeReadingOrderSettingsSetHorizontalDilationThresholdSingle.restype = None
_lib.BridgeReadingOrderSettingsSetHorizontalDilationThresholdSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeReadingOrderSettingsGetTextDirection.restype = ctypes.c_int32
_lib.BridgeReadingOrderSettingsGetTextDirection.argtypes = [ctypes.c_void_p]

_lib.BridgeReadingOrderSettingsSetTextDirectionTextDirection.restype = None
_lib.BridgeReadingOrderSettingsSetTextDirectionTextDirection.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class ReadingOrderSettings:
    """
    Merged view of ReadingOrderSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate ReadingOrderSettings directly. Use static factory methods instead."""
        raise TypeError("ReadingOrderSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeReadingOrderSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeReadingOrderSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeReadingOrderSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise ReadingOrderSettingsError(f"ReadingOrderSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("ReadingOrderSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_horizontal_dilation_threshold(self) -> float:
        """
        Gets the HorizontalDilationThreshold property.

        Returns:
            float: The value of the HorizontalDilationThreshold property.

        Raises:
            ReadingOrderSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeReadingOrderSettingsGetHorizontalDilationThreshold(self._handle)
        self._check_error()
        return result

    def set_horizontal_dilation_threshold(self, value: float) -> None:
        """
        Sets the HorizontalDilationThreshold property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            ReadingOrderSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeReadingOrderSettingsSetHorizontalDilationThresholdSingle(self._handle, value)
        self._check_error()

    def get_text_direction(self) -> Any:
        """
        Gets the TextDirection property.

        Returns:
            Any: The value of the TextDirection property.

        Raises:
            ReadingOrderSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeReadingOrderSettingsGetTextDirection(self._handle)
        self._check_error()
        return result

    def set_text_direction(self, value: Any) -> None:
        """
        Sets the TextDirection property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            ReadingOrderSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeReadingOrderSettingsSetTextDirectionTextDirection(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    @property
    def horizontal_dilation_threshold(self) -> float:
        """
        Gets the HorizontalDilationThreshold property.

        Returns:
            float: The value of the HorizontalDilationThreshold property.
        """
        return self.get_horizontal_dilation_threshold()

    @horizontal_dilation_threshold.setter
    def horizontal_dilation_threshold(self, value: float) -> None:
        """
        Sets the horizontal dilation threshold.

        Args:
            value (float): The value to set.
        """
        self.set_horizontal_dilation_threshold(value)

    @property
    def text_direction(self) -> Any:
        """
        Gets the TextDirection property.

        Returns:
            Any: The value of the TextDirection property.
        """
        return self.get_text_direction()

    @text_direction.setter
    def text_direction(self, value: Any) -> None:
        """
        Sets the text direction.

        Args:
            value (Any): The value to set.
        """
        self.set_text_direction(value)



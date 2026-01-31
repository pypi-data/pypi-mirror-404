"""
TableRecognitionSettings module.
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


class TableRecognitionSettingsError(Exception):
    """Exception raised by TableRecognitionSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeTableRecognitionSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeTableRecognitionSettingsGetLastErrorCode.argtypes = []

_lib.BridgeTableRecognitionSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeTableRecognitionSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeTableRecognitionSettingsFreeErrorString.restype = None
_lib.BridgeTableRecognitionSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeTableRecognitionSettingsGetTargetSize.restype = ctypes.c_int32
_lib.BridgeTableRecognitionSettingsGetTargetSize.argtypes = [ctypes.c_void_p]

_lib.BridgeTableRecognitionSettingsSetTargetSizeInt32.restype = None
_lib.BridgeTableRecognitionSettingsSetTargetSizeInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class TableRecognitionSettings:
    """
    Merged view of TableRecognitionSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate TableRecognitionSettings directly. Use static factory methods instead."""
        raise TypeError("TableRecognitionSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeTableRecognitionSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeTableRecognitionSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeTableRecognitionSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise TableRecognitionSettingsError(f"TableRecognitionSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("TableRecognitionSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_target_size(self) -> int:
        """
        Gets the TargetSize property.

        Returns:
            int: The value of the TargetSize property.

        Raises:
            TableRecognitionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeTableRecognitionSettingsGetTargetSize(self._handle)
        self._check_error()
        return result

    def set_target_size(self, value: int) -> None:
        """
        Sets the TargetSize property.

        Args:
            value (int)

        Returns:
            None: The result of the operation

        Raises:
            TableRecognitionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeTableRecognitionSettingsSetTargetSizeInt32(self._handle, value)
        self._check_error()

    @property
    def target_size(self) -> int:
        """
        Gets the TargetSize property.

        Returns:
            int: The value of the TargetSize property.
        """
        return self.get_target_size()

    @target_size.setter
    def target_size(self, value: int) -> None:
        """
        Sets the target size.

        Args:
            value (int): The value to set.
        """
        self.set_target_size(value)



"""
Jbig2Settings module.
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


class Jbig2SettingsError(Exception):
    """Exception raised by Jbig2Settings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeJbig2SettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeJbig2SettingsGetLastErrorCode.argtypes = []

_lib.BridgeJbig2SettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeJbig2SettingsGetLastErrorMessage.argtypes = []

_lib.BridgeJbig2SettingsFreeErrorString.restype = None
_lib.BridgeJbig2SettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeJbig2SettingsGetJbig2PmsThreshold.restype = ctypes.c_float
_lib.BridgeJbig2SettingsGetJbig2PmsThreshold.argtypes = [ctypes.c_void_p]

_lib.BridgeJbig2SettingsSetJbig2PmsThresholdSingle.restype = None
_lib.BridgeJbig2SettingsSetJbig2PmsThresholdSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]


class Jbig2Settings:
    """
    Merged view of Jbig2Settings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate Jbig2Settings directly. Use static factory methods instead."""
        raise TypeError("Jbig2Settings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeJbig2SettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeJbig2SettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeJbig2SettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise Jbig2SettingsError(f"Jbig2Settings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("Jbig2Settings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_jbig2_pms_threshold(self) -> float:
        """
        Gets the Jbig2PmsThreshold property.

        Returns:
            float: The value of the Jbig2PmsThreshold property.

        Raises:
            Jbig2SettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeJbig2SettingsGetJbig2PmsThreshold(self._handle)
        self._check_error()
        return result

    def set_jbig2_pms_threshold(self, value: float) -> None:
        """
        Sets the Jbig2PmsThreshold property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            Jbig2SettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeJbig2SettingsSetJbig2PmsThresholdSingle(self._handle, value)
        self._check_error()

    @property
    def jbig2_pms_threshold(self) -> float:
        """
        Gets the Jbig2PmsThreshold property.

        Returns:
            float: The value of the Jbig2PmsThreshold property.
        """
        return self.get_jbig2_pms_threshold()

    @jbig2_pms_threshold.setter
    def jbig2_pms_threshold(self, value: float) -> None:
        """
        Sets the jbig2 pms threshold.

        Args:
            value (float): The value to set.
        """
        self.set_jbig2_pms_threshold(value)



"""
InferenceLayoutSettings module.
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


class InferenceLayoutSettingsError(Exception):
    """Exception raised by InferenceLayoutSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeInferenceLayoutSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeInferenceLayoutSettingsGetLastErrorCode.argtypes = []

_lib.BridgeInferenceLayoutSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeInferenceLayoutSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeInferenceLayoutSettingsFreeErrorString.restype = None
_lib.BridgeInferenceLayoutSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeInferenceLayoutSettingsGetConfidenceThreshold.restype = ctypes.c_float
_lib.BridgeInferenceLayoutSettingsGetConfidenceThreshold.argtypes = [ctypes.c_void_p]

_lib.BridgeInferenceLayoutSettingsSetConfidenceThresholdSingle.restype = None
_lib.BridgeInferenceLayoutSettingsSetConfidenceThresholdSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]


class InferenceLayoutSettings:
    """
    Merged view of InferenceLayoutSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate InferenceLayoutSettings directly. Use static factory methods instead."""
        raise TypeError("InferenceLayoutSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeInferenceLayoutSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeInferenceLayoutSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeInferenceLayoutSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise InferenceLayoutSettingsError(f"InferenceLayoutSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("InferenceLayoutSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_confidence_threshold(self) -> float:
        """
        Gets the ConfidenceThreshold property.

        Returns:
            float: The value of the ConfidenceThreshold property.

        Raises:
            InferenceLayoutSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeInferenceLayoutSettingsGetConfidenceThreshold(self._handle)
        self._check_error()
        return result

    def set_confidence_threshold(self, value: float) -> None:
        """
        Sets the ConfidenceThreshold property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            InferenceLayoutSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeInferenceLayoutSettingsSetConfidenceThresholdSingle(self._handle, value)
        self._check_error()

    @property
    def confidence_threshold(self) -> float:
        """
        Gets the ConfidenceThreshold property.

        Returns:
            float: The value of the ConfidenceThreshold property.
        """
        return self.get_confidence_threshold()

    @confidence_threshold.setter
    def confidence_threshold(self, value: float) -> None:
        """
        Sets the confidence threshold.

        Args:
            value (float): The value to set.
        """
        self.set_confidence_threshold(value)



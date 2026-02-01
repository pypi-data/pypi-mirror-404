"""
SegmenterSettings module.
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


class SegmenterSettingsError(Exception):
    """Exception raised by SegmenterSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeSegmenterSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeSegmenterSettingsGetLastErrorCode.argtypes = []

_lib.BridgeSegmenterSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeSegmenterSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeSegmenterSettingsFreeErrorString.restype = None
_lib.BridgeSegmenterSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeSegmenterSettingsGetTargetSize.restype = ctypes.c_int32
_lib.BridgeSegmenterSettingsGetTargetSize.argtypes = [ctypes.c_void_p]

_lib.BridgeSegmenterSettingsSetTargetSizeInt32.restype = None
_lib.BridgeSegmenterSettingsSetTargetSizeInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeSegmenterSettingsGetConfidenceThreshold.restype = ctypes.c_float
_lib.BridgeSegmenterSettingsGetConfidenceThreshold.argtypes = [ctypes.c_void_p]

_lib.BridgeSegmenterSettingsSetConfidenceThresholdSingle.restype = None
_lib.BridgeSegmenterSettingsSetConfidenceThresholdSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeSegmenterSettingsGetUseCpuOnly.restype = ctypes.c_bool
_lib.BridgeSegmenterSettingsGetUseCpuOnly.argtypes = [ctypes.c_void_p]

_lib.BridgeSegmenterSettingsSetUseCpuOnlyBoolean.restype = None
_lib.BridgeSegmenterSettingsSetUseCpuOnlyBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeSegmenterSettingsGetMinimumZoneSize.restype = ctypes.c_int32
_lib.BridgeSegmenterSettingsGetMinimumZoneSize.argtypes = [ctypes.c_void_p]

_lib.BridgeSegmenterSettingsSetMinimumZoneSizeInt32.restype = None
_lib.BridgeSegmenterSettingsSetMinimumZoneSizeInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeSegmenterSettingsGetDetectOrientation.restype = ctypes.c_bool
_lib.BridgeSegmenterSettingsGetDetectOrientation.argtypes = [ctypes.c_void_p]

_lib.BridgeSegmenterSettingsSetDetectOrientationBoolean.restype = None
_lib.BridgeSegmenterSettingsSetDetectOrientationBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]


class SegmenterSettings:
    """
    Merged view of SegmenterSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate SegmenterSettings directly. Use static factory methods instead."""
        raise TypeError("SegmenterSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeSegmenterSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSegmenterSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSegmenterSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SegmenterSettingsError(f"SegmenterSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("SegmenterSettings instance has been closed")

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
            SegmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSegmenterSettingsGetTargetSize(self._handle)
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
            SegmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSegmenterSettingsSetTargetSizeInt32(self._handle, value)
        self._check_error()

    def get_confidence_threshold(self) -> float:
        """
        Gets the ConfidenceThreshold property.

        Returns:
            float: The value of the ConfidenceThreshold property.

        Raises:
            SegmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSegmenterSettingsGetConfidenceThreshold(self._handle)
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
            SegmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSegmenterSettingsSetConfidenceThresholdSingle(self._handle, value)
        self._check_error()

    def get_use_cpu_only(self) -> bool:
        """
        Gets the UseCpuOnly property.

        Returns:
            bool: The value of the UseCpuOnly property.

        Raises:
            SegmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSegmenterSettingsGetUseCpuOnly(self._handle)
        self._check_error()
        return result

    def set_use_cpu_only(self, value: bool) -> None:
        """
        Sets the UseCpuOnly property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            SegmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSegmenterSettingsSetUseCpuOnlyBoolean(self._handle, value)
        self._check_error()

    def get_minimum_zone_size(self) -> int:
        """
        Gets the MinimumZoneSize property.

        Returns:
            int: The value of the MinimumZoneSize property.

        Raises:
            SegmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSegmenterSettingsGetMinimumZoneSize(self._handle)
        self._check_error()
        return result

    def set_minimum_zone_size(self, value: int) -> None:
        """
        Sets the MinimumZoneSize property.

        Args:
            value (int)

        Returns:
            None: The result of the operation

        Raises:
            SegmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSegmenterSettingsSetMinimumZoneSizeInt32(self._handle, value)
        self._check_error()

    def get_detect_orientation(self) -> bool:
        """
        Gets the DetectOrientation property.

        Returns:
            bool: The value of the DetectOrientation property.

        Raises:
            SegmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSegmenterSettingsGetDetectOrientation(self._handle)
        self._check_error()
        return result

    def set_detect_orientation(self, value: bool) -> None:
        """
        Sets the DetectOrientation property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            SegmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSegmenterSettingsSetDetectOrientationBoolean(self._handle, value)
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

    @property
    def use_cpu_only(self) -> bool:
        """
        Gets the UseCpuOnly property.

        Returns:
            bool: The value of the UseCpuOnly property.
        """
        return self.get_use_cpu_only()

    @use_cpu_only.setter
    def use_cpu_only(self, value: bool) -> None:
        """
        Sets the use cpu only.

        Args:
            value (bool): The value to set.
        """
        self.set_use_cpu_only(value)

    @property
    def minimum_zone_size(self) -> int:
        """
        Gets the MinimumZoneSize property.

        Returns:
            int: The value of the MinimumZoneSize property.
        """
        return self.get_minimum_zone_size()

    @minimum_zone_size.setter
    def minimum_zone_size(self, value: int) -> None:
        """
        Sets the minimum zone size.

        Args:
            value (int): The value to set.
        """
        self.set_minimum_zone_size(value)

    @property
    def detect_orientation(self) -> bool:
        """
        Gets the DetectOrientation property.

        Returns:
            bool: The value of the DetectOrientation property.
        """
        return self.get_detect_orientation()

    @detect_orientation.setter
    def detect_orientation(self, value: bool) -> None:
        """
        Sets the detect orientation.

        Args:
            value (bool): The value to set.
        """
        self.set_detect_orientation(value)



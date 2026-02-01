"""
OcrSettings module.
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


class OcrSettingsError(Exception):
    """Exception raised by OcrSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeOcrSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeOcrSettingsGetLastErrorCode.argtypes = []

_lib.BridgeOcrSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeOcrSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeOcrSettingsFreeErrorString.restype = None
_lib.BridgeOcrSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeOcrSettingsGetDefaultLanguages.restype = ctypes.c_void_p
_lib.BridgeOcrSettingsGetDefaultLanguages.argtypes = [ctypes.c_void_p]

_lib.BridgeOcrSettingsSetDefaultLanguagesString.restype = None
_lib.BridgeOcrSettingsSetDefaultLanguagesString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOcrSettingsGetFavorAccuracy.restype = ctypes.c_bool
_lib.BridgeOcrSettingsGetFavorAccuracy.argtypes = [ctypes.c_void_p]

_lib.BridgeOcrSettingsSetFavorAccuracyBoolean.restype = None
_lib.BridgeOcrSettingsSetFavorAccuracyBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeOcrSettingsGetEnablePreprocessing.restype = ctypes.c_bool
_lib.BridgeOcrSettingsGetEnablePreprocessing.argtypes = [ctypes.c_void_p]

_lib.BridgeOcrSettingsSetEnablePreprocessingBoolean.restype = None
_lib.BridgeOcrSettingsSetEnablePreprocessingBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeOcrSettingsGetEnableSkewDetection.restype = ctypes.c_bool
_lib.BridgeOcrSettingsGetEnableSkewDetection.argtypes = [ctypes.c_void_p]

_lib.BridgeOcrSettingsSetEnableSkewDetectionBoolean.restype = None
_lib.BridgeOcrSettingsSetEnableSkewDetectionBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeOcrSettingsGetEnableTableDetection.restype = ctypes.c_bool
_lib.BridgeOcrSettingsGetEnableTableDetection.argtypes = [ctypes.c_void_p]

_lib.BridgeOcrSettingsSetEnableTableDetectionBoolean.restype = None
_lib.BridgeOcrSettingsSetEnableTableDetectionBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]


class OcrSettings:
    """
    Merged view of OcrSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate OcrSettings directly. Use static factory methods instead."""
        raise TypeError("OcrSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeOcrSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeOcrSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeOcrSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise OcrSettingsError(f"OcrSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("OcrSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_default_languages(self) -> str:
        """
        Gets the DefaultLanguages property.

        Returns:
            str: The value of the DefaultLanguages property.

        Raises:
            OcrSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOcrSettingsGetDefaultLanguages(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_default_languages(self, value: str) -> None:
        """
        Sets the DefaultLanguages property.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            OcrSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOcrSettingsSetDefaultLanguagesString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_favor_accuracy(self) -> bool:
        """
        Gets the FavorAccuracy property.

        Returns:
            bool: The value of the FavorAccuracy property.

        Raises:
            OcrSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOcrSettingsGetFavorAccuracy(self._handle)
        self._check_error()
        return result

    def set_favor_accuracy(self, value: bool) -> None:
        """
        Sets the FavorAccuracy property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            OcrSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOcrSettingsSetFavorAccuracyBoolean(self._handle, value)
        self._check_error()

    def get_enable_preprocessing(self) -> bool:
        """
        Gets the EnablePreprocessing property.

        Returns:
            bool: The value of the EnablePreprocessing property.

        Raises:
            OcrSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOcrSettingsGetEnablePreprocessing(self._handle)
        self._check_error()
        return result

    def set_enable_preprocessing(self, value: bool) -> None:
        """
        Sets the EnablePreprocessing property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            OcrSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOcrSettingsSetEnablePreprocessingBoolean(self._handle, value)
        self._check_error()

    def get_enable_skew_detection(self) -> bool:
        """
        Gets the EnableSkewDetection property.

        Returns:
            bool: The value of the EnableSkewDetection property.

        Raises:
            OcrSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOcrSettingsGetEnableSkewDetection(self._handle)
        self._check_error()
        return result

    def set_enable_skew_detection(self, value: bool) -> None:
        """
        Sets the EnableSkewDetection property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            OcrSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOcrSettingsSetEnableSkewDetectionBoolean(self._handle, value)
        self._check_error()

    def get_enable_table_detection(self) -> bool:
        """
        Gets the EnableTableDetection property.

        Returns:
            bool: The value of the EnableTableDetection property.

        Raises:
            OcrSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOcrSettingsGetEnableTableDetection(self._handle)
        self._check_error()
        return result

    def set_enable_table_detection(self, value: bool) -> None:
        """
        Sets the EnableTableDetection property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            OcrSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOcrSettingsSetEnableTableDetectionBoolean(self._handle, value)
        self._check_error()

    @property
    def default_languages(self) -> str:
        """
        Gets the DefaultLanguages property.

        Returns:
            str: The value of the DefaultLanguages property.
        """
        return self.get_default_languages()

    @default_languages.setter
    def default_languages(self, value: str) -> None:
        """
        Sets the default languages.

        Args:
            value (str): The value to set.
        """
        self.set_default_languages(value)

    @property
    def favor_accuracy(self) -> bool:
        """
        Gets the FavorAccuracy property.

        Returns:
            bool: The value of the FavorAccuracy property.
        """
        return self.get_favor_accuracy()

    @favor_accuracy.setter
    def favor_accuracy(self, value: bool) -> None:
        """
        Sets the favor accuracy.

        Args:
            value (bool): The value to set.
        """
        self.set_favor_accuracy(value)

    @property
    def enable_preprocessing(self) -> bool:
        """
        Gets the EnablePreprocessing property.

        Returns:
            bool: The value of the EnablePreprocessing property.
        """
        return self.get_enable_preprocessing()

    @enable_preprocessing.setter
    def enable_preprocessing(self, value: bool) -> None:
        """
        Sets the enable preprocessing.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_preprocessing(value)

    @property
    def enable_skew_detection(self) -> bool:
        """
        Gets the EnableSkewDetection property.

        Returns:
            bool: The value of the EnableSkewDetection property.
        """
        return self.get_enable_skew_detection()

    @enable_skew_detection.setter
    def enable_skew_detection(self, value: bool) -> None:
        """
        Sets the enable skew detection.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_skew_detection(value)

    @property
    def enable_table_detection(self) -> bool:
        """
        Gets the EnableTableDetection property.

        Returns:
            bool: The value of the EnableTableDetection property.
        """
        return self.get_enable_table_detection()

    @enable_table_detection.setter
    def enable_table_detection(self, value: bool) -> None:
        """
        Sets the enable table detection.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_table_detection(value)



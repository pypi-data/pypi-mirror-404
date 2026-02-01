"""
ContentExtractionSettings module.
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


class ContentExtractionSettingsError(Exception):
    """Exception raised by ContentExtractionSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeContentExtractionSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeContentExtractionSettingsGetLastErrorCode.argtypes = []

_lib.BridgeContentExtractionSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeContentExtractionSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeContentExtractionSettingsFreeErrorString.restype = None
_lib.BridgeContentExtractionSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeContentExtractionSettingsGetEnableOcrExtraction.restype = ctypes.c_bool
_lib.BridgeContentExtractionSettingsGetEnableOcrExtraction.argtypes = [ctypes.c_void_p]

_lib.BridgeContentExtractionSettingsSetEnableOcrExtractionBoolean.restype = None
_lib.BridgeContentExtractionSettingsSetEnableOcrExtractionBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeContentExtractionSettingsGetEnableImageExtraction.restype = ctypes.c_bool
_lib.BridgeContentExtractionSettingsGetEnableImageExtraction.argtypes = [ctypes.c_void_p]

_lib.BridgeContentExtractionSettingsSetEnableImageExtractionBoolean.restype = None
_lib.BridgeContentExtractionSettingsSetEnableImageExtractionBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeContentExtractionSettingsGetEnableTableExtraction.restype = ctypes.c_bool
_lib.BridgeContentExtractionSettingsGetEnableTableExtraction.argtypes = [ctypes.c_void_p]

_lib.BridgeContentExtractionSettingsSetEnableTableExtractionBoolean.restype = None
_lib.BridgeContentExtractionSettingsSetEnableTableExtractionBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeContentExtractionSettingsGetMinimumZoneConfidence.restype = ctypes.c_float
_lib.BridgeContentExtractionSettingsGetMinimumZoneConfidence.argtypes = [ctypes.c_void_p]

_lib.BridgeContentExtractionSettingsSetMinimumZoneConfidenceSingle.restype = None
_lib.BridgeContentExtractionSettingsSetMinimumZoneConfidenceSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeContentExtractionSettingsGetEnableFullPageOcrFallback.restype = ctypes.c_bool
_lib.BridgeContentExtractionSettingsGetEnableFullPageOcrFallback.argtypes = [ctypes.c_void_p]

_lib.BridgeContentExtractionSettingsSetEnableFullPageOcrFallbackBoolean.restype = None
_lib.BridgeContentExtractionSettingsSetEnableFullPageOcrFallbackBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]


class ContentExtractionSettings:
    """
    Merged view of ContentExtractionSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate ContentExtractionSettings directly. Use static factory methods instead."""
        raise TypeError("ContentExtractionSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeContentExtractionSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeContentExtractionSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeContentExtractionSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise ContentExtractionSettingsError(f"ContentExtractionSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("ContentExtractionSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_enable_ocr_extraction(self) -> bool:
        """
        Gets the EnableOcrExtraction property.

        Returns:
            bool: The value of the EnableOcrExtraction property.

        Raises:
            ContentExtractionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeContentExtractionSettingsGetEnableOcrExtraction(self._handle)
        self._check_error()
        return result

    def set_enable_ocr_extraction(self, value: bool) -> None:
        """
        Sets the EnableOcrExtraction property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            ContentExtractionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeContentExtractionSettingsSetEnableOcrExtractionBoolean(self._handle, value)
        self._check_error()

    def get_enable_image_extraction(self) -> bool:
        """
        Gets the EnableImageExtraction property.

        Returns:
            bool: The value of the EnableImageExtraction property.

        Raises:
            ContentExtractionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeContentExtractionSettingsGetEnableImageExtraction(self._handle)
        self._check_error()
        return result

    def set_enable_image_extraction(self, value: bool) -> None:
        """
        Sets the EnableImageExtraction property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            ContentExtractionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeContentExtractionSettingsSetEnableImageExtractionBoolean(self._handle, value)
        self._check_error()

    def get_enable_table_extraction(self) -> bool:
        """
        Gets the EnableTableExtraction property.

        Returns:
            bool: The value of the EnableTableExtraction property.

        Raises:
            ContentExtractionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeContentExtractionSettingsGetEnableTableExtraction(self._handle)
        self._check_error()
        return result

    def set_enable_table_extraction(self, value: bool) -> None:
        """
        Sets the EnableTableExtraction property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            ContentExtractionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeContentExtractionSettingsSetEnableTableExtractionBoolean(self._handle, value)
        self._check_error()

    def get_minimum_zone_confidence(self) -> float:
        """
        Gets the MinimumZoneConfidence property.

        Returns:
            float: The value of the MinimumZoneConfidence property.

        Raises:
            ContentExtractionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeContentExtractionSettingsGetMinimumZoneConfidence(self._handle)
        self._check_error()
        return result

    def set_minimum_zone_confidence(self, value: float) -> None:
        """
        Sets the MinimumZoneConfidence property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            ContentExtractionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeContentExtractionSettingsSetMinimumZoneConfidenceSingle(self._handle, value)
        self._check_error()

    def get_enable_full_page_ocr_fallback(self) -> bool:
        """
        Gets the EnableFullPageOcrFallback property.

        Returns:
            bool: The value of the EnableFullPageOcrFallback property.

        Raises:
            ContentExtractionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeContentExtractionSettingsGetEnableFullPageOcrFallback(self._handle)
        self._check_error()
        return result

    def set_enable_full_page_ocr_fallback(self, value: bool) -> None:
        """
        Sets the EnableFullPageOcrFallback property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            ContentExtractionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeContentExtractionSettingsSetEnableFullPageOcrFallbackBoolean(self._handle, value)
        self._check_error()

    @property
    def enable_ocr_extraction(self) -> bool:
        """
        Gets the EnableOcrExtraction property.

        Returns:
            bool: The value of the EnableOcrExtraction property.
        """
        return self.get_enable_ocr_extraction()

    @enable_ocr_extraction.setter
    def enable_ocr_extraction(self, value: bool) -> None:
        """
        Sets the enable ocr extraction.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_ocr_extraction(value)

    @property
    def enable_image_extraction(self) -> bool:
        """
        Gets the EnableImageExtraction property.

        Returns:
            bool: The value of the EnableImageExtraction property.
        """
        return self.get_enable_image_extraction()

    @enable_image_extraction.setter
    def enable_image_extraction(self, value: bool) -> None:
        """
        Sets the enable image extraction.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_image_extraction(value)

    @property
    def enable_table_extraction(self) -> bool:
        """
        Gets the EnableTableExtraction property.

        Returns:
            bool: The value of the EnableTableExtraction property.
        """
        return self.get_enable_table_extraction()

    @enable_table_extraction.setter
    def enable_table_extraction(self, value: bool) -> None:
        """
        Sets the enable table extraction.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_table_extraction(value)

    @property
    def minimum_zone_confidence(self) -> float:
        """
        Gets the MinimumZoneConfidence property.

        Returns:
            float: The value of the MinimumZoneConfidence property.
        """
        return self.get_minimum_zone_confidence()

    @minimum_zone_confidence.setter
    def minimum_zone_confidence(self, value: float) -> None:
        """
        Sets the minimum zone confidence.

        Args:
            value (float): The value to set.
        """
        self.set_minimum_zone_confidence(value)

    @property
    def enable_full_page_ocr_fallback(self) -> bool:
        """
        Gets the EnableFullPageOcrFallback property.

        Returns:
            bool: The value of the EnableFullPageOcrFallback property.
        """
        return self.get_enable_full_page_ocr_fallback()

    @enable_full_page_ocr_fallback.setter
    def enable_full_page_ocr_fallback(self, value: bool) -> None:
        """
        Sets the enable full page ocr fallback.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_full_page_ocr_fallback(value)



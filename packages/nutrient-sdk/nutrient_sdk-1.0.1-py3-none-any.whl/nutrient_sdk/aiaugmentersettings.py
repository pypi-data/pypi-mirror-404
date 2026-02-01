"""
AiAugmenterSettings module.
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


class AiAugmenterSettingsError(Exception):
    """Exception raised by AiAugmenterSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeAiAugmenterSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeAiAugmenterSettingsGetLastErrorCode.argtypes = []

_lib.BridgeAiAugmenterSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeAiAugmenterSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeAiAugmenterSettingsFreeErrorString.restype = None
_lib.BridgeAiAugmenterSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeAiAugmenterSettingsGetEnableVlmClassification.restype = ctypes.c_bool
_lib.BridgeAiAugmenterSettingsGetEnableVlmClassification.argtypes = [ctypes.c_void_p]

_lib.BridgeAiAugmenterSettingsSetEnableVlmClassificationBoolean.restype = None
_lib.BridgeAiAugmenterSettingsSetEnableVlmClassificationBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeAiAugmenterSettingsGetEnableContentDescription.restype = ctypes.c_bool
_lib.BridgeAiAugmenterSettingsGetEnableContentDescription.argtypes = [ctypes.c_void_p]

_lib.BridgeAiAugmenterSettingsSetEnableContentDescriptionBoolean.restype = None
_lib.BridgeAiAugmenterSettingsSetEnableContentDescriptionBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeAiAugmenterSettingsGetClassificationConfidence.restype = ctypes.c_float
_lib.BridgeAiAugmenterSettingsGetClassificationConfidence.argtypes = [ctypes.c_void_p]

_lib.BridgeAiAugmenterSettingsSetClassificationConfidenceSingle.restype = None
_lib.BridgeAiAugmenterSettingsSetClassificationConfidenceSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeAiAugmenterSettingsGetEnableLanguageDetection.restype = ctypes.c_bool
_lib.BridgeAiAugmenterSettingsGetEnableLanguageDetection.argtypes = [ctypes.c_void_p]

_lib.BridgeAiAugmenterSettingsSetEnableLanguageDetectionBoolean.restype = None
_lib.BridgeAiAugmenterSettingsSetEnableLanguageDetectionBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeAiAugmenterSettingsGetEnableReadingOrder.restype = ctypes.c_bool
_lib.BridgeAiAugmenterSettingsGetEnableReadingOrder.argtypes = [ctypes.c_void_p]

_lib.BridgeAiAugmenterSettingsSetEnableReadingOrderBoolean.restype = None
_lib.BridgeAiAugmenterSettingsSetEnableReadingOrderBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeAiAugmenterSettingsGetEnableRelationshipDetection.restype = ctypes.c_bool
_lib.BridgeAiAugmenterSettingsGetEnableRelationshipDetection.argtypes = [ctypes.c_void_p]

_lib.BridgeAiAugmenterSettingsSetEnableRelationshipDetectionBoolean.restype = None
_lib.BridgeAiAugmenterSettingsSetEnableRelationshipDetectionBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]


class AiAugmenterSettings:
    """
    Merged view of AiAugmenterSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate AiAugmenterSettings directly. Use static factory methods instead."""
        raise TypeError("AiAugmenterSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeAiAugmenterSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeAiAugmenterSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeAiAugmenterSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise AiAugmenterSettingsError(f"AiAugmenterSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("AiAugmenterSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_enable_vlm_classification(self) -> bool:
        """
        Gets the EnableVlmClassification property.

        Returns:
            bool: The value of the EnableVlmClassification property.

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeAiAugmenterSettingsGetEnableVlmClassification(self._handle)
        self._check_error()
        return result

    def set_enable_vlm_classification(self, value: bool) -> None:
        """
        Sets the EnableVlmClassification property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeAiAugmenterSettingsSetEnableVlmClassificationBoolean(self._handle, value)
        self._check_error()

    def get_enable_content_description(self) -> bool:
        """
        Gets the EnableContentDescription property.

        Returns:
            bool: The value of the EnableContentDescription property.

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeAiAugmenterSettingsGetEnableContentDescription(self._handle)
        self._check_error()
        return result

    def set_enable_content_description(self, value: bool) -> None:
        """
        Sets the EnableContentDescription property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeAiAugmenterSettingsSetEnableContentDescriptionBoolean(self._handle, value)
        self._check_error()

    def get_classification_confidence(self) -> float:
        """
        Gets the ClassificationConfidence property.

        Returns:
            float: The value of the ClassificationConfidence property.

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeAiAugmenterSettingsGetClassificationConfidence(self._handle)
        self._check_error()
        return result

    def set_classification_confidence(self, value: float) -> None:
        """
        Sets the ClassificationConfidence property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeAiAugmenterSettingsSetClassificationConfidenceSingle(self._handle, value)
        self._check_error()

    def get_enable_language_detection(self) -> bool:
        """
        Gets the EnableLanguageDetection property.

        Returns:
            bool: The value of the EnableLanguageDetection property.

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeAiAugmenterSettingsGetEnableLanguageDetection(self._handle)
        self._check_error()
        return result

    def set_enable_language_detection(self, value: bool) -> None:
        """
        Sets the EnableLanguageDetection property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeAiAugmenterSettingsSetEnableLanguageDetectionBoolean(self._handle, value)
        self._check_error()

    def get_enable_reading_order(self) -> bool:
        """
        Gets the EnableReadingOrder property.

        Returns:
            bool: The value of the EnableReadingOrder property.

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeAiAugmenterSettingsGetEnableReadingOrder(self._handle)
        self._check_error()
        return result

    def set_enable_reading_order(self, value: bool) -> None:
        """
        Sets the EnableReadingOrder property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeAiAugmenterSettingsSetEnableReadingOrderBoolean(self._handle, value)
        self._check_error()

    def get_enable_relationship_detection(self) -> bool:
        """
        Gets the EnableRelationshipDetection property.

        Returns:
            bool: The value of the EnableRelationshipDetection property.

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeAiAugmenterSettingsGetEnableRelationshipDetection(self._handle)
        self._check_error()
        return result

    def set_enable_relationship_detection(self, value: bool) -> None:
        """
        Sets the EnableRelationshipDetection property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            AiAugmenterSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeAiAugmenterSettingsSetEnableRelationshipDetectionBoolean(self._handle, value)
        self._check_error()

    @property
    def enable_vlm_classification(self) -> bool:
        """
        Gets the EnableVlmClassification property.

        Returns:
            bool: The value of the EnableVlmClassification property.
        """
        return self.get_enable_vlm_classification()

    @enable_vlm_classification.setter
    def enable_vlm_classification(self, value: bool) -> None:
        """
        Sets the enable vlm classification.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_vlm_classification(value)

    @property
    def enable_content_description(self) -> bool:
        """
        Gets the EnableContentDescription property.

        Returns:
            bool: The value of the EnableContentDescription property.
        """
        return self.get_enable_content_description()

    @enable_content_description.setter
    def enable_content_description(self, value: bool) -> None:
        """
        Sets the enable content description.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_content_description(value)

    @property
    def classification_confidence(self) -> float:
        """
        Gets the ClassificationConfidence property.

        Returns:
            float: The value of the ClassificationConfidence property.
        """
        return self.get_classification_confidence()

    @classification_confidence.setter
    def classification_confidence(self, value: float) -> None:
        """
        Sets the classification confidence.

        Args:
            value (float): The value to set.
        """
        self.set_classification_confidence(value)

    @property
    def enable_language_detection(self) -> bool:
        """
        Gets the EnableLanguageDetection property.

        Returns:
            bool: The value of the EnableLanguageDetection property.
        """
        return self.get_enable_language_detection()

    @enable_language_detection.setter
    def enable_language_detection(self, value: bool) -> None:
        """
        Sets the enable language detection.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_language_detection(value)

    @property
    def enable_reading_order(self) -> bool:
        """
        Gets the EnableReadingOrder property.

        Returns:
            bool: The value of the EnableReadingOrder property.
        """
        return self.get_enable_reading_order()

    @enable_reading_order.setter
    def enable_reading_order(self, value: bool) -> None:
        """
        Sets the enable reading order.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_reading_order(value)

    @property
    def enable_relationship_detection(self) -> bool:
        """
        Gets the EnableRelationshipDetection property.

        Returns:
            bool: The value of the EnableRelationshipDetection property.
        """
        return self.get_enable_relationship_detection()

    @enable_relationship_detection.setter
    def enable_relationship_detection(self, value: bool) -> None:
        """
        Sets the enable relationship detection.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_relationship_detection(value)



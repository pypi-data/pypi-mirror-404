"""
VisionSettings module.
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


class VisionSettingsError(Exception):
    """Exception raised by VisionSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeVisionSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeVisionSettingsGetLastErrorCode.argtypes = []

_lib.BridgeVisionSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeVisionSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeVisionSettingsFreeErrorString.restype = None
_lib.BridgeVisionSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionSettingsGetProvider.restype = ctypes.c_int32
_lib.BridgeVisionSettingsGetProvider.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionSettingsSetProviderVlmProvider.restype = None
_lib.BridgeVisionSettingsSetProviderVlmProvider.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeVisionSettingsGetFeatures.restype = ctypes.c_int32
_lib.BridgeVisionSettingsGetFeatures.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionSettingsSetFeaturesVisionFeatures.restype = None
_lib.BridgeVisionSettingsSetFeaturesVisionFeatures.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeVisionSettingsGetEngine.restype = ctypes.c_int32
_lib.BridgeVisionSettingsGetEngine.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionSettingsSetEngineVisionEngine.restype = None
_lib.BridgeVisionSettingsSetEngineVisionEngine.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class VisionSettings:
    """
    Merged view of VisionSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate VisionSettings directly. Use static factory methods instead."""
        raise TypeError("VisionSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeVisionSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeVisionSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeVisionSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise VisionSettingsError(f"VisionSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("VisionSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_provider(self) -> Any:
        """
        Gets the Provider property.

        Returns:
            Any: The value of the Provider property.

        Raises:
            VisionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeVisionSettingsGetProvider(self._handle)
        self._check_error()
        return result

    def set_provider(self, value: Any) -> None:
        """
        Sets the Provider property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            VisionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeVisionSettingsSetProviderVlmProvider(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_features(self) -> Any:
        """
        Gets the Features property.

        Returns:
            Any: The value of the Features property.

        Raises:
            VisionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeVisionSettingsGetFeatures(self._handle)
        self._check_error()
        return result

    def set_features(self, value: Any) -> None:
        """
        Sets the Features property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            VisionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeVisionSettingsSetFeaturesVisionFeatures(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_engine(self) -> Any:
        """
        Gets the Engine property.

        Returns:
            Any: The value of the Engine property.

        Raises:
            VisionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeVisionSettingsGetEngine(self._handle)
        self._check_error()
        return result

    def set_engine(self, value: Any) -> None:
        """
        Sets the Engine property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            VisionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeVisionSettingsSetEngineVisionEngine(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    @property
    def provider(self) -> Any:
        """
        Gets the Provider property.

        Returns:
            Any: The value of the Provider property.
        """
        return self.get_provider()

    @provider.setter
    def provider(self, value: Any) -> None:
        """
        Sets the provider.

        Args:
            value (Any): The value to set.
        """
        self.set_provider(value)

    @property
    def features(self) -> Any:
        """
        Gets the Features property.

        Returns:
            Any: The value of the Features property.
        """
        return self.get_features()

    @features.setter
    def features(self, value: Any) -> None:
        """
        Sets the features.

        Args:
            value (Any): The value to set.
        """
        self.set_features(value)

    @property
    def engine(self) -> Any:
        """
        Gets the Engine property.

        Returns:
            Any: The value of the Engine property.
        """
        return self.get_engine()

    @engine.setter
    def engine(self, value: Any) -> None:
        """
        Sets the engine.

        Args:
            value (Any): The value to set.
        """
        self.set_engine(value)



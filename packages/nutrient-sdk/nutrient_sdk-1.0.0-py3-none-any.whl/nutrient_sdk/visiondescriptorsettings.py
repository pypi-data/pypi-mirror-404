"""
VisionDescriptorSettings module.
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


class VisionDescriptorSettingsError(Exception):
    """Exception raised by VisionDescriptorSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeVisionDescriptorSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeVisionDescriptorSettingsGetLastErrorCode.argtypes = []

_lib.BridgeVisionDescriptorSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeVisionDescriptorSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeVisionDescriptorSettingsFreeErrorString.restype = None
_lib.BridgeVisionDescriptorSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionDescriptorSettingsGetLevel.restype = ctypes.c_int32
_lib.BridgeVisionDescriptorSettingsGetLevel.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionDescriptorSettingsSetLevelDescriptionLevel.restype = None
_lib.BridgeVisionDescriptorSettingsSetLevelDescriptionLevel.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeVisionDescriptorSettingsGetStandardPrompt.restype = ctypes.c_void_p
_lib.BridgeVisionDescriptorSettingsGetStandardPrompt.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionDescriptorSettingsSetStandardPromptString.restype = None
_lib.BridgeVisionDescriptorSettingsSetStandardPromptString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeVisionDescriptorSettingsGetDetailedPrompt.restype = ctypes.c_void_p
_lib.BridgeVisionDescriptorSettingsGetDetailedPrompt.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionDescriptorSettingsSetDetailedPromptString.restype = None
_lib.BridgeVisionDescriptorSettingsSetDetailedPromptString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


class VisionDescriptorSettings:
    """
    Merged view of VisionDescriptorSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate VisionDescriptorSettings directly. Use static factory methods instead."""
        raise TypeError("VisionDescriptorSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeVisionDescriptorSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeVisionDescriptorSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeVisionDescriptorSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise VisionDescriptorSettingsError(f"VisionDescriptorSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("VisionDescriptorSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_level(self) -> Any:
        """
        Gets the Level property.

        Returns:
            Any: The value of the Level property.

        Raises:
            VisionDescriptorSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeVisionDescriptorSettingsGetLevel(self._handle)
        self._check_error()
        return result

    def set_level(self, value: Any) -> None:
        """
        Sets the Level property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            VisionDescriptorSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeVisionDescriptorSettingsSetLevelDescriptionLevel(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_standard_prompt(self) -> str:
        """
        Gets the StandardPrompt property.

        Returns:
            str: The value of the StandardPrompt property.

        Raises:
            VisionDescriptorSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeVisionDescriptorSettingsGetStandardPrompt(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_standard_prompt(self, value: str) -> None:
        """
        Sets the StandardPrompt property.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            VisionDescriptorSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeVisionDescriptorSettingsSetStandardPromptString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_detailed_prompt(self) -> str:
        """
        Gets the DetailedPrompt property.

        Returns:
            str: The value of the DetailedPrompt property.

        Raises:
            VisionDescriptorSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeVisionDescriptorSettingsGetDetailedPrompt(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_detailed_prompt(self, value: str) -> None:
        """
        Sets the DetailedPrompt property.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            VisionDescriptorSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeVisionDescriptorSettingsSetDetailedPromptString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    @property
    def level(self) -> Any:
        """
        Gets the Level property.

        Returns:
            Any: The value of the Level property.
        """
        return self.get_level()

    @level.setter
    def level(self, value: Any) -> None:
        """
        Sets the level.

        Args:
            value (Any): The value to set.
        """
        self.set_level(value)

    @property
    def standard_prompt(self) -> str:
        """
        Gets the StandardPrompt property.

        Returns:
            str: The value of the StandardPrompt property.
        """
        return self.get_standard_prompt()

    @standard_prompt.setter
    def standard_prompt(self, value: str) -> None:
        """
        Sets the standard prompt.

        Args:
            value (str): The value to set.
        """
        self.set_standard_prompt(value)

    @property
    def detailed_prompt(self) -> str:
        """
        Gets the DetailedPrompt property.

        Returns:
            str: The value of the DetailedPrompt property.
        """
        return self.get_detailed_prompt()

    @detailed_prompt.setter
    def detailed_prompt(self, value: str) -> None:
        """
        Sets the detailed prompt.

        Args:
            value (str): The value to set.
        """
        self.set_detailed_prompt(value)



"""
OpenAIApiEndpointSettings module.
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


class OpenAIApiEndpointSettingsError(Exception):
    """Exception raised by OpenAIApiEndpointSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeOpenAIApiEndpointSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeOpenAIApiEndpointSettingsGetLastErrorCode.argtypes = []

_lib.BridgeOpenAIApiEndpointSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeOpenAIApiEndpointSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeOpenAIApiEndpointSettingsFreeErrorString.restype = None
_lib.BridgeOpenAIApiEndpointSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsGetApiKey.restype = ctypes.c_void_p
_lib.BridgeOpenAIApiEndpointSettingsGetApiKey.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsSetApiKeyString.restype = None
_lib.BridgeOpenAIApiEndpointSettingsSetApiKeyString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsGetApiEndpoint.restype = ctypes.c_void_p
_lib.BridgeOpenAIApiEndpointSettingsGetApiEndpoint.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsSetApiEndpointString.restype = None
_lib.BridgeOpenAIApiEndpointSettingsSetApiEndpointString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsGetModel.restype = ctypes.c_void_p
_lib.BridgeOpenAIApiEndpointSettingsGetModel.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsSetModelString.restype = None
_lib.BridgeOpenAIApiEndpointSettingsSetModelString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsGetTemperature.restype = ctypes.c_double
_lib.BridgeOpenAIApiEndpointSettingsGetTemperature.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsSetTemperatureDouble.restype = None
_lib.BridgeOpenAIApiEndpointSettingsSetTemperatureDouble.argtypes = [ctypes.c_void_p, ctypes.c_double]

_lib.BridgeOpenAIApiEndpointSettingsGetMaxTokens.restype = ctypes.c_int32
_lib.BridgeOpenAIApiEndpointSettingsGetMaxTokens.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsSetMaxTokensInt32.restype = None
_lib.BridgeOpenAIApiEndpointSettingsSetMaxTokensInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeOpenAIApiEndpointSettingsGetSystemPrompt.restype = ctypes.c_void_p
_lib.BridgeOpenAIApiEndpointSettingsGetSystemPrompt.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsSetSystemPromptString.restype = None
_lib.BridgeOpenAIApiEndpointSettingsSetSystemPromptString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsGetStream.restype = ctypes.c_bool
_lib.BridgeOpenAIApiEndpointSettingsGetStream.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIApiEndpointSettingsSetStreamBoolean.restype = None
_lib.BridgeOpenAIApiEndpointSettingsSetStreamBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]


class OpenAIApiEndpointSettings:
    """
    Merged view of OpenAIApiEndpointSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate OpenAIApiEndpointSettings directly. Use static factory methods instead."""
        raise TypeError("OpenAIApiEndpointSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeOpenAIApiEndpointSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeOpenAIApiEndpointSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeOpenAIApiEndpointSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise OpenAIApiEndpointSettingsError(f"OpenAIApiEndpointSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("OpenAIApiEndpointSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_api_key(self) -> str:
        """
        Gets the ApiKey property.

        Returns:
            str: The value of the ApiKey property.

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIApiEndpointSettingsGetApiKey(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_api_key(self, value: str) -> None:
        """
        Sets the ApiKey property.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIApiEndpointSettingsSetApiKeyString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_api_endpoint(self) -> str:
        """
        Gets the ApiEndpoint property.

        Returns:
            str: The value of the ApiEndpoint property.

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIApiEndpointSettingsGetApiEndpoint(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_api_endpoint(self, value: str) -> None:
        """
        Sets the ApiEndpoint property.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIApiEndpointSettingsSetApiEndpointString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_model(self) -> str:
        """
        Gets the Model property.

        Returns:
            str: The value of the Model property.

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIApiEndpointSettingsGetModel(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_model(self, value: str) -> None:
        """
        Sets the Model property.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIApiEndpointSettingsSetModelString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_temperature(self) -> float:
        """
        Gets the Temperature property.

        Returns:
            float: The value of the Temperature property.

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIApiEndpointSettingsGetTemperature(self._handle)
        self._check_error()
        return result

    def set_temperature(self, value: float) -> None:
        """
        Sets the Temperature property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIApiEndpointSettingsSetTemperatureDouble(self._handle, value)
        self._check_error()

    def get_max_tokens(self) -> int:
        """
        Gets the MaxTokens property.

        Returns:
            int: The value of the MaxTokens property.

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIApiEndpointSettingsGetMaxTokens(self._handle)
        self._check_error()
        return result

    def set_max_tokens(self, value: int) -> None:
        """
        Sets the MaxTokens property.

        Args:
            value (int)

        Returns:
            None: The result of the operation

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIApiEndpointSettingsSetMaxTokensInt32(self._handle, value)
        self._check_error()

    def get_system_prompt(self) -> str:
        """
        Gets the SystemPrompt property.

        Returns:
            str: The value of the SystemPrompt property.

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIApiEndpointSettingsGetSystemPrompt(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_system_prompt(self, value: str) -> None:
        """
        Sets the SystemPrompt property.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIApiEndpointSettingsSetSystemPromptString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_stream(self) -> bool:
        """
        Gets the Stream property.

        Returns:
            bool: The value of the Stream property.

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIApiEndpointSettingsGetStream(self._handle)
        self._check_error()
        return result

    def set_stream(self, value: bool) -> None:
        """
        Sets the Stream property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            OpenAIApiEndpointSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIApiEndpointSettingsSetStreamBoolean(self._handle, value)
        self._check_error()

    @property
    def api_key(self) -> str:
        """
        Gets the ApiKey property.

        Returns:
            str: The value of the ApiKey property.
        """
        return self.get_api_key()

    @api_key.setter
    def api_key(self, value: str) -> None:
        """
        Sets the api key.

        Args:
            value (str): The value to set.
        """
        self.set_api_key(value)

    @property
    def api_endpoint(self) -> str:
        """
        Gets the ApiEndpoint property.

        Returns:
            str: The value of the ApiEndpoint property.
        """
        return self.get_api_endpoint()

    @api_endpoint.setter
    def api_endpoint(self, value: str) -> None:
        """
        Sets the api endpoint.

        Args:
            value (str): The value to set.
        """
        self.set_api_endpoint(value)

    @property
    def model(self) -> str:
        """
        Gets the Model property.

        Returns:
            str: The value of the Model property.
        """
        return self.get_model()

    @model.setter
    def model(self, value: str) -> None:
        """
        Sets the model.

        Args:
            value (str): The value to set.
        """
        self.set_model(value)

    @property
    def temperature(self) -> float:
        """
        Gets the Temperature property.

        Returns:
            float: The value of the Temperature property.
        """
        return self.get_temperature()

    @temperature.setter
    def temperature(self, value: float) -> None:
        """
        Sets the temperature.

        Args:
            value (float): The value to set.
        """
        self.set_temperature(value)

    @property
    def max_tokens(self) -> int:
        """
        Gets the MaxTokens property.

        Returns:
            int: The value of the MaxTokens property.
        """
        return self.get_max_tokens()

    @max_tokens.setter
    def max_tokens(self, value: int) -> None:
        """
        Sets the max tokens.

        Args:
            value (int): The value to set.
        """
        self.set_max_tokens(value)

    @property
    def system_prompt(self) -> str:
        """
        Gets the SystemPrompt property.

        Returns:
            str: The value of the SystemPrompt property.
        """
        return self.get_system_prompt()

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        """
        Sets the system prompt.

        Args:
            value (str): The value to set.
        """
        self.set_system_prompt(value)

    @property
    def stream(self) -> bool:
        """
        Gets the Stream property.

        Returns:
            bool: The value of the Stream property.
        """
        return self.get_stream()

    @stream.setter
    def stream(self, value: bool) -> None:
        """
        Sets the stream.

        Args:
            value (bool): The value to set.
        """
        self.set_stream(value)



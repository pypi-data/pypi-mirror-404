"""
OpenAILanguagesDetectionSettings module.
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


class OpenAILanguagesDetectionSettingsError(Exception):
    """Exception raised by OpenAILanguagesDetectionSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeOpenAILanguagesDetectionSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeOpenAILanguagesDetectionSettingsGetLastErrorCode.argtypes = []

_lib.BridgeOpenAILanguagesDetectionSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeOpenAILanguagesDetectionSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeOpenAILanguagesDetectionSettingsFreeErrorString.restype = None
_lib.BridgeOpenAILanguagesDetectionSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAILanguagesDetectionSettingsGetApiKey.restype = ctypes.c_void_p
_lib.BridgeOpenAILanguagesDetectionSettingsGetApiKey.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAILanguagesDetectionSettingsSetApiKeyString.restype = None
_lib.BridgeOpenAILanguagesDetectionSettingsSetApiKeyString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOpenAILanguagesDetectionSettingsGetApiEndpoint.restype = ctypes.c_void_p
_lib.BridgeOpenAILanguagesDetectionSettingsGetApiEndpoint.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAILanguagesDetectionSettingsSetApiEndpointString.restype = None
_lib.BridgeOpenAILanguagesDetectionSettingsSetApiEndpointString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOpenAILanguagesDetectionSettingsGetModel.restype = ctypes.c_void_p
_lib.BridgeOpenAILanguagesDetectionSettingsGetModel.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAILanguagesDetectionSettingsSetModelString.restype = None
_lib.BridgeOpenAILanguagesDetectionSettingsSetModelString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOpenAILanguagesDetectionSettingsGetMaxTokens.restype = ctypes.c_int32
_lib.BridgeOpenAILanguagesDetectionSettingsGetMaxTokens.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAILanguagesDetectionSettingsSetMaxTokensInt32.restype = None
_lib.BridgeOpenAILanguagesDetectionSettingsSetMaxTokensInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeOpenAILanguagesDetectionSettingsGetTemperature.restype = ctypes.c_double
_lib.BridgeOpenAILanguagesDetectionSettingsGetTemperature.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAILanguagesDetectionSettingsSetTemperatureDouble.restype = None
_lib.BridgeOpenAILanguagesDetectionSettingsSetTemperatureDouble.argtypes = [ctypes.c_void_p, ctypes.c_double]

_lib.BridgeOpenAILanguagesDetectionSettingsGetDetail.restype = ctypes.c_void_p
_lib.BridgeOpenAILanguagesDetectionSettingsGetDetail.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAILanguagesDetectionSettingsSetDetailString.restype = None
_lib.BridgeOpenAILanguagesDetectionSettingsSetDetailString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


class OpenAILanguagesDetectionSettings:
    """
    Merged view of OpenAILanguagesDetectionSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate OpenAILanguagesDetectionSettings directly. Use static factory methods instead."""
        raise TypeError("OpenAILanguagesDetectionSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeOpenAILanguagesDetectionSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeOpenAILanguagesDetectionSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeOpenAILanguagesDetectionSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise OpenAILanguagesDetectionSettingsError(f"OpenAILanguagesDetectionSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("OpenAILanguagesDetectionSettings instance has been closed")

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
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAILanguagesDetectionSettingsGetApiKey(self._handle)
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
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAILanguagesDetectionSettingsSetApiKeyString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_api_endpoint(self) -> str:
        """
        Gets the ApiEndpoint property.

        Returns:
            str: The value of the ApiEndpoint property.

        Raises:
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAILanguagesDetectionSettingsGetApiEndpoint(self._handle)
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
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAILanguagesDetectionSettingsSetApiEndpointString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_model(self) -> str:
        """
        Gets the Model property.

        Returns:
            str: The value of the Model property.

        Raises:
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAILanguagesDetectionSettingsGetModel(self._handle)
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
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAILanguagesDetectionSettingsSetModelString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_max_tokens(self) -> int:
        """
        Gets the MaxTokens property.

        Returns:
            int: The value of the MaxTokens property.

        Raises:
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAILanguagesDetectionSettingsGetMaxTokens(self._handle)
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
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAILanguagesDetectionSettingsSetMaxTokensInt32(self._handle, value)
        self._check_error()

    def get_temperature(self) -> float:
        """
        Gets the Temperature property.

        Returns:
            float: The value of the Temperature property.

        Raises:
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAILanguagesDetectionSettingsGetTemperature(self._handle)
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
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAILanguagesDetectionSettingsSetTemperatureDouble(self._handle, value)
        self._check_error()

    def get_detail(self) -> str:
        """
        Gets the Detail property.

        Returns:
            str: The value of the Detail property.

        Raises:
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAILanguagesDetectionSettingsGetDetail(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_detail(self, value: str) -> None:
        """
        Sets the Detail property.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            OpenAILanguagesDetectionSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAILanguagesDetectionSettingsSetDetailString(self._handle, value.encode('utf-8') if value else None)
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
    def detail(self) -> str:
        """
        Gets the Detail property.

        Returns:
            str: The value of the Detail property.
        """
        return self.get_detail()

    @detail.setter
    def detail(self, value: str) -> None:
        """
        Sets the detail.

        Args:
            value (str): The value to set.
        """
        self.set_detail(value)



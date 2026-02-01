"""
OpenAIPictureAltSettings module.
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


class OpenAIPictureAltSettingsError(Exception):
    """Exception raised by OpenAIPictureAltSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeOpenAIPictureAltSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeOpenAIPictureAltSettingsGetLastErrorCode.argtypes = []

_lib.BridgeOpenAIPictureAltSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeOpenAIPictureAltSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeOpenAIPictureAltSettingsFreeErrorString.restype = None
_lib.BridgeOpenAIPictureAltSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIPictureAltSettingsGetApiKey.restype = ctypes.c_void_p
_lib.BridgeOpenAIPictureAltSettingsGetApiKey.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIPictureAltSettingsSetApiKeyString.restype = None
_lib.BridgeOpenAIPictureAltSettingsSetApiKeyString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOpenAIPictureAltSettingsGetApiEndpoint.restype = ctypes.c_void_p
_lib.BridgeOpenAIPictureAltSettingsGetApiEndpoint.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIPictureAltSettingsSetApiEndpointString.restype = None
_lib.BridgeOpenAIPictureAltSettingsSetApiEndpointString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOpenAIPictureAltSettingsGetModel.restype = ctypes.c_void_p
_lib.BridgeOpenAIPictureAltSettingsGetModel.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIPictureAltSettingsSetModelString.restype = None
_lib.BridgeOpenAIPictureAltSettingsSetModelString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeOpenAIPictureAltSettingsGetMaxTokens.restype = ctypes.c_int32
_lib.BridgeOpenAIPictureAltSettingsGetMaxTokens.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIPictureAltSettingsSetMaxTokensInt32.restype = None
_lib.BridgeOpenAIPictureAltSettingsSetMaxTokensInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeOpenAIPictureAltSettingsGetTemperature.restype = ctypes.c_double
_lib.BridgeOpenAIPictureAltSettingsGetTemperature.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIPictureAltSettingsSetTemperatureDouble.restype = None
_lib.BridgeOpenAIPictureAltSettingsSetTemperatureDouble.argtypes = [ctypes.c_void_p, ctypes.c_double]

_lib.BridgeOpenAIPictureAltSettingsGetDetail.restype = ctypes.c_void_p
_lib.BridgeOpenAIPictureAltSettingsGetDetail.argtypes = [ctypes.c_void_p]

_lib.BridgeOpenAIPictureAltSettingsSetDetailString.restype = None
_lib.BridgeOpenAIPictureAltSettingsSetDetailString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


class OpenAIPictureAltSettings:
    """
    Merged view of OpenAIPictureAltSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate OpenAIPictureAltSettings directly. Use static factory methods instead."""
        raise TypeError("OpenAIPictureAltSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeOpenAIPictureAltSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeOpenAIPictureAltSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeOpenAIPictureAltSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise OpenAIPictureAltSettingsError(f"OpenAIPictureAltSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("OpenAIPictureAltSettings instance has been closed")

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
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIPictureAltSettingsGetApiKey(self._handle)
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
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIPictureAltSettingsSetApiKeyString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_api_endpoint(self) -> str:
        """
        Gets the ApiEndpoint property.

        Returns:
            str: The value of the ApiEndpoint property.

        Raises:
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIPictureAltSettingsGetApiEndpoint(self._handle)
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
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIPictureAltSettingsSetApiEndpointString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_model(self) -> str:
        """
        Gets the Model property.

        Returns:
            str: The value of the Model property.

        Raises:
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIPictureAltSettingsGetModel(self._handle)
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
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIPictureAltSettingsSetModelString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_max_tokens(self) -> int:
        """
        Gets the MaxTokens property.

        Returns:
            int: The value of the MaxTokens property.

        Raises:
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIPictureAltSettingsGetMaxTokens(self._handle)
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
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIPictureAltSettingsSetMaxTokensInt32(self._handle, value)
        self._check_error()

    def get_temperature(self) -> float:
        """
        Gets the Temperature property.

        Returns:
            float: The value of the Temperature property.

        Raises:
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIPictureAltSettingsGetTemperature(self._handle)
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
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIPictureAltSettingsSetTemperatureDouble(self._handle, value)
        self._check_error()

    def get_detail(self) -> str:
        """
        Gets the Detail property.

        Returns:
            str: The value of the Detail property.

        Raises:
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeOpenAIPictureAltSettingsGetDetail(self._handle)
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
            OpenAIPictureAltSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeOpenAIPictureAltSettingsSetDetailString(self._handle, value.encode('utf-8') if value else None)
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



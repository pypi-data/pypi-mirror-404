"""
TimestampConfiguration module.
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


class TimestampConfigurationError(Exception):
    """Exception raised by TimestampConfiguration operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeTimestampConfigurationInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeTimestampConfigurationInitNSDKH.argtypes = []

_lib.BridgeTimestampConfigurationCloseNSDKH.restype = None
_lib.BridgeTimestampConfigurationCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeTimestampConfigurationGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeTimestampConfigurationGetLastErrorCode.argtypes = []

_lib.BridgeTimestampConfigurationGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeTimestampConfigurationGetLastErrorMessage.argtypes = []

_lib.BridgeTimestampConfigurationFreeErrorString.restype = None
_lib.BridgeTimestampConfigurationFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeTimestampConfigurationGetServerUrl.restype = ctypes.c_void_p
_lib.BridgeTimestampConfigurationGetServerUrl.argtypes = [ctypes.c_void_p]

_lib.BridgeTimestampConfigurationSetServerUrlString.restype = None
_lib.BridgeTimestampConfigurationSetServerUrlString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeTimestampConfigurationGetUsername.restype = ctypes.c_void_p
_lib.BridgeTimestampConfigurationGetUsername.argtypes = [ctypes.c_void_p]

_lib.BridgeTimestampConfigurationSetUsernameString.restype = None
_lib.BridgeTimestampConfigurationSetUsernameString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeTimestampConfigurationGetPassword.restype = ctypes.c_void_p
_lib.BridgeTimestampConfigurationGetPassword.argtypes = [ctypes.c_void_p]

_lib.BridgeTimestampConfigurationSetPasswordString.restype = None
_lib.BridgeTimestampConfigurationSetPasswordString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


class TimestampConfiguration:
    """
    Configuration for adding a trusted timestamp to a digital signature. When configured, the signature will include a timestamp from a Time Stamp Authority (TSA), enabling PAdES-T (PDF Advanced Electronic Signatures with Timestamp) compliance.
    """

    def __init__(self):
        """Initialize a new TimestampConfiguration instance."""
        self._handle = _lib.BridgeTimestampConfigurationInitNSDKH()
        if not self._handle:
            self._check_error()
        self._closed = False

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        """Close and cleanup the native resources."""
        if not self._closed and self._handle:
            _lib.BridgeTimestampConfigurationCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeTimestampConfigurationGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeTimestampConfigurationGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeTimestampConfigurationFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise TimestampConfigurationError(f"TimestampConfiguration: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("TimestampConfiguration instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_server_url(self) -> str:
        """
        Gets the URL of the Time Stamp Authority (TSA) server.

        Returns:
            str: The value of the ServerUrl property.

        Raises:
            TimestampConfigurationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeTimestampConfigurationGetServerUrl(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_server_url(self, value: str) -> None:
        """
        Sets the URL of the Time Stamp Authority (TSA) server.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            TimestampConfigurationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeTimestampConfigurationSetServerUrlString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_username(self) -> str:
        """
        Gets the username for authentication with the TSA server, if required.

        Returns:
            str: The value of the Username property.

        Raises:
            TimestampConfigurationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeTimestampConfigurationGetUsername(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_username(self, value: str) -> None:
        """
        Sets the username for authentication with the TSA server, if required.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            TimestampConfigurationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeTimestampConfigurationSetUsernameString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_password(self) -> str:
        """
        Gets the password for authentication with the TSA server, if required.

        Returns:
            str: The value of the Password property.

        Raises:
            TimestampConfigurationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeTimestampConfigurationGetPassword(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_password(self, value: str) -> None:
        """
        Sets the password for authentication with the TSA server, if required.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            TimestampConfigurationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeTimestampConfigurationSetPasswordString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    @property
    def server_url(self) -> str:
        """
        Gets the URL of the Time Stamp Authority (TSA) server.

        Returns:
            str: The value of the ServerUrl property.
        """
        return self.get_server_url()

    @server_url.setter
    def server_url(self, value: str) -> None:
        """
        Sets the server url.

        Args:
            value (str): The value to set.
        """
        self.set_server_url(value)

    @property
    def username(self) -> str:
        """
        Gets the username for authentication with the TSA server, if required.

        Returns:
            str: The value of the Username property.
        """
        return self.get_username()

    @username.setter
    def username(self, value: str) -> None:
        """
        Sets the username.

        Args:
            value (str): The value to set.
        """
        self.set_username(value)

    @property
    def password(self) -> str:
        """
        Gets the password for authentication with the TSA server, if required.

        Returns:
            str: The value of the Password property.
        """
        return self.get_password()

    @password.setter
    def password(self, value: str) -> None:
        """
        Sets the password.

        Args:
            value (str): The value to set.
        """
        self.set_password(value)



"""
License module.
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


class LicenseError(Exception):
    """Exception raised by License operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeLicenseInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeLicenseInitNSDKH.argtypes = []

_lib.BridgeLicenseCloseNSDKH.restype = None
_lib.BridgeLicenseCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeLicenseGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeLicenseGetLastErrorCode.argtypes = []

_lib.BridgeLicenseGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeLicenseGetLastErrorMessage.argtypes = []

_lib.BridgeLicenseFreeErrorString.restype = None
_lib.BridgeLicenseFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeLicenseRegisterKeyString.restype = None
_lib.BridgeLicenseRegisterKeyString.argtypes = [ctypes.c_void_p]

_lib.BridgeLicenseInitializeLicenseInt32String.restype = None
_lib.BridgeLicenseInitializeLicenseInt32String.argtypes = [ctypes.c_int32, ctypes.c_void_p]

_lib.BridgeLicenseTraceFeatures.restype = ctypes.c_void_p
_lib.BridgeLicenseTraceFeatures.argtypes = []


class License:
    """
    Manages licensing for the Nutrient Native SDK. Provides methods to register license keys and trace licensed features in evaluation mode (without registering a key).
    """

    def __init__(self):
        """Initialize a new License instance."""
        self._handle = _lib.BridgeLicenseInitNSDKH()
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
            _lib.BridgeLicenseCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeLicenseGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeLicenseGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeLicenseFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise LicenseError(f"License: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("License instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    @classmethod
    def register_key(cls, key: str) -> None:
        """
        Unlocks the SDK with a commercial or a demo license key. You can subsequently use this method to unlock the underlying implementation.

        Args:
            key (str)

        Returns:
            None: The result of the operation

        Raises:
            LicenseError: If the operation fails
        """

        _lib.BridgeLicenseRegisterKeyString(key.encode('utf-8') if key else None)
        error_code = _lib.BridgeLicenseGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeLicenseGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeLicenseFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise LicenseError(f"RegisterKey: {message} (code: {error_code})")

    @classmethod
    def initialize_license(cls, sdk_id: int, sdk_version: str) -> None:
        """
        Internal Use Only

        Args:
            sdk_id (int)
            sdk_version (str)

        Returns:
            None: The result of the operation

        Raises:
            LicenseError: If the operation fails
        """

        _lib.BridgeLicenseInitializeLicenseInt32String(sdk_id, sdk_version.encode('utf-8') if sdk_version else None)
        error_code = _lib.BridgeLicenseGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeLicenseGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeLicenseFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise LicenseError(f"InitializeLicense: {message} (code: {error_code})")

    @classmethod
    def trace_features(cls) -> str:
        """
        When the SDK is in trial mode, this method returns a string that lists the features that have been evaluated during the session.

        Returns:
            str: The result of the operation

        Raises:
            LicenseError: If the operation fails
        """

        result = _lib.BridgeLicenseTraceFeatures()
        error_code = _lib.BridgeLicenseGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeLicenseGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeLicenseFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise LicenseError(f"TraceFeatures: {message} (code: {error_code})")
        return sdk_loader.convert_string_handle(result)



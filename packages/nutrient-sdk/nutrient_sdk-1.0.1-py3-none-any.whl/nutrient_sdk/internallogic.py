"""
InternalLogic module.
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


class InternalLogicError(Exception):
    """Exception raised by InternalLogic operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeInternalLogicInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeInternalLogicInitNSDKH.argtypes = []

_lib.BridgeInternalLogicCloseNSDKH.restype = None
_lib.BridgeInternalLogicCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeInternalLogicGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeInternalLogicGetLastErrorCode.argtypes = []

_lib.BridgeInternalLogicGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeInternalLogicGetLastErrorMessage.argtypes = []

_lib.BridgeInternalLogicFreeErrorString.restype = None
_lib.BridgeInternalLogicFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeInternalLogicInitializationInt32String.restype = None
_lib.BridgeInternalLogicInitializationInt32String.argtypes = [ctypes.c_int32, ctypes.c_void_p]


class InternalLogic:
    """InternalLogic."""

    def __init__(self):
        """Initialize a new InternalLogic instance."""
        self._handle = _lib.BridgeInternalLogicInitNSDKH()
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
            _lib.BridgeInternalLogicCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeInternalLogicGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeInternalLogicGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeInternalLogicFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise InternalLogicError(f"InternalLogic: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("InternalLogic instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    @classmethod
    def initialization(cls, sdk_id: int, sdk_version: str) -> None:
        """
        Args:
            sdk_id (int)
            sdk_version (str)

        Returns:
            None: The result of the operation

        Raises:
            InternalLogicError: If the operation fails
        """

        _lib.BridgeInternalLogicInitializationInt32String(sdk_id, sdk_version.encode('utf-8') if sdk_version else None)
        error_code = _lib.BridgeInternalLogicGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeInternalLogicGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeInternalLogicFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise InternalLogicError(f"Initialization: {message} (code: {error_code})")



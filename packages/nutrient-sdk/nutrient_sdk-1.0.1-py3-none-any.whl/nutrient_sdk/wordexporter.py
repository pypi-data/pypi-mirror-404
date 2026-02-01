"""
WordExporter module.
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


class WordExporterError(Exception):
    """Exception raised by WordExporter operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeWordExporterInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeWordExporterInitNSDKH.argtypes = []

_lib.BridgeWordExporterCloseNSDKH.restype = None
_lib.BridgeWordExporterCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeWordExporterGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeWordExporterGetLastErrorCode.argtypes = []

_lib.BridgeWordExporterGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeWordExporterGetLastErrorMessage.argtypes = []

_lib.BridgeWordExporterFreeErrorString.restype = None
_lib.BridgeWordExporterFreeErrorString.argtypes = [ctypes.c_void_p]


class WordExporter:
    """
    Exports documents to Microsoft Word format (.docx) preserving formatting and structure.
    """

    def __init__(self):
        """Initialize a new WordExporter instance."""
        self._handle = _lib.BridgeWordExporterInitNSDKH()
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
            _lib.BridgeWordExporterCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeWordExporterGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeWordExporterGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeWordExporterFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise WordExporterError(f"WordExporter: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("WordExporter instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance



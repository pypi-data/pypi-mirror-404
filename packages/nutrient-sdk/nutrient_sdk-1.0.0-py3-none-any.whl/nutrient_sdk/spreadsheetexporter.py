"""
SpreadsheetExporter module.
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


class SpreadsheetExporterError(Exception):
    """Exception raised by SpreadsheetExporter operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeSpreadsheetExporterInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeSpreadsheetExporterInitNSDKH.argtypes = []

_lib.BridgeSpreadsheetExporterCloseNSDKH.restype = None
_lib.BridgeSpreadsheetExporterCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetExporterGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeSpreadsheetExporterGetLastErrorCode.argtypes = []

_lib.BridgeSpreadsheetExporterGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeSpreadsheetExporterGetLastErrorMessage.argtypes = []

_lib.BridgeSpreadsheetExporterFreeErrorString.restype = None
_lib.BridgeSpreadsheetExporterFreeErrorString.argtypes = [ctypes.c_void_p]


class SpreadsheetExporter:
    """
    Exports documents to spreadsheet formats including Excel (.xlsx) and CSV.
    """

    def __init__(self):
        """Initialize a new SpreadsheetExporter instance."""
        self._handle = _lib.BridgeSpreadsheetExporterInitNSDKH()
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
            _lib.BridgeSpreadsheetExporterCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeSpreadsheetExporterGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSpreadsheetExporterGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSpreadsheetExporterFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SpreadsheetExporterError(f"SpreadsheetExporter: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("SpreadsheetExporter instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance



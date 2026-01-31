"""
HtmlExporter module.
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


class HtmlExporterError(Exception):
    """Exception raised by HtmlExporter operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeHtmlExporterInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeHtmlExporterInitNSDKH.argtypes = []

_lib.BridgeHtmlExporterCloseNSDKH.restype = None
_lib.BridgeHtmlExporterCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeHtmlExporterGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeHtmlExporterGetLastErrorCode.argtypes = []

_lib.BridgeHtmlExporterGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeHtmlExporterGetLastErrorMessage.argtypes = []

_lib.BridgeHtmlExporterFreeErrorString.restype = None
_lib.BridgeHtmlExporterFreeErrorString.argtypes = [ctypes.c_void_p]


class HtmlExporter:
    """
    Exports documents to HTML format with optional CSS styling and embedded resources.
    """

    def __init__(self):
        """Initialize a new HtmlExporter instance."""
        self._handle = _lib.BridgeHtmlExporterInitNSDKH()
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
            _lib.BridgeHtmlExporterCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeHtmlExporterGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeHtmlExporterGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeHtmlExporterFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise HtmlExporterError(f"HtmlExporter: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("HtmlExporter instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance



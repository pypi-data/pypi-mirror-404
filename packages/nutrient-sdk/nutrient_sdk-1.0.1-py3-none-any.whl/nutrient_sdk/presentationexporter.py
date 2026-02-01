"""
PresentationExporter module.
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


class PresentationExporterError(Exception):
    """Exception raised by PresentationExporter operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePresentationExporterInitNSDKH.restype = ctypes.c_void_p
_lib.BridgePresentationExporterInitNSDKH.argtypes = []

_lib.BridgePresentationExporterCloseNSDKH.restype = None
_lib.BridgePresentationExporterCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgePresentationExporterGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePresentationExporterGetLastErrorCode.argtypes = []

_lib.BridgePresentationExporterGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePresentationExporterGetLastErrorMessage.argtypes = []

_lib.BridgePresentationExporterFreeErrorString.restype = None
_lib.BridgePresentationExporterFreeErrorString.argtypes = [ctypes.c_void_p]


class PresentationExporter:
    """
    Exports documents to presentation formats including PowerPoint (.pptx).
    """

    def __init__(self):
        """Initialize a new PresentationExporter instance."""
        self._handle = _lib.BridgePresentationExporterInitNSDKH()
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
            _lib.BridgePresentationExporterCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgePresentationExporterGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePresentationExporterGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePresentationExporterFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PresentationExporterError(f"PresentationExporter: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PresentationExporter instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance



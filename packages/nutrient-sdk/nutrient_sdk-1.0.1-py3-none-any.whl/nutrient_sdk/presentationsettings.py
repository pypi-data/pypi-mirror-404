"""
PresentationSettings module.
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


class PresentationSettingsError(Exception):
    """Exception raised by PresentationSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePresentationSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePresentationSettingsGetLastErrorCode.argtypes = []

_lib.BridgePresentationSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePresentationSettingsGetLastErrorMessage.argtypes = []

_lib.BridgePresentationSettingsFreeErrorString.restype = None
_lib.BridgePresentationSettingsFreeErrorString.argtypes = [ctypes.c_void_p]


class PresentationSettings:
    """
    Merged view of PresentationSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate PresentationSettings directly. Use static factory methods instead."""
        raise TypeError("PresentationSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePresentationSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePresentationSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePresentationSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PresentationSettingsError(f"PresentationSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PresentationSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance



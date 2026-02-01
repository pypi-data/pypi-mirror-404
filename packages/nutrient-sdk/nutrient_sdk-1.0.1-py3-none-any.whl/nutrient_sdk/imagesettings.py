"""
ImageSettings module.
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


class ImageSettingsError(Exception):
    """Exception raised by ImageSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeImageSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeImageSettingsGetLastErrorCode.argtypes = []

_lib.BridgeImageSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeImageSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeImageSettingsFreeErrorString.restype = None
_lib.BridgeImageSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeImageSettingsGetMode.restype = ctypes.c_int32
_lib.BridgeImageSettingsGetMode.argtypes = [ctypes.c_void_p]

_lib.BridgeImageSettingsSetModeImageSettingMode.restype = None
_lib.BridgeImageSettingsSetModeImageSettingMode.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeImageSettingsGetRasterizationDpi.restype = ctypes.c_float
_lib.BridgeImageSettingsGetRasterizationDpi.argtypes = [ctypes.c_void_p]

_lib.BridgeImageSettingsSetRasterizationDpiSingle.restype = None
_lib.BridgeImageSettingsSetRasterizationDpiSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeImageSettingsGetExportFormat.restype = ctypes.c_int32
_lib.BridgeImageSettingsGetExportFormat.argtypes = [ctypes.c_void_p]

_lib.BridgeImageSettingsSetExportFormatImageExportFormat.restype = None
_lib.BridgeImageSettingsSetExportFormatImageExportFormat.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class ImageSettings:
    """
    Merged view of ImageSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate ImageSettings directly. Use static factory methods instead."""
        raise TypeError("ImageSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeImageSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeImageSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeImageSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise ImageSettingsError(f"ImageSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("ImageSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_mode(self) -> Any:
        """
        Gets the Mode property.

        Returns:
            Any: The value of the Mode property.

        Raises:
            ImageSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeImageSettingsGetMode(self._handle)
        self._check_error()
        return result

    def set_mode(self, value: Any) -> None:
        """
        Sets the Mode property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            ImageSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeImageSettingsSetModeImageSettingMode(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_rasterization_dpi(self) -> float:
        """
        Gets the RasterizationDpi property.

        Returns:
            float: The value of the RasterizationDpi property.

        Raises:
            ImageSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeImageSettingsGetRasterizationDpi(self._handle)
        self._check_error()
        return result

    def set_rasterization_dpi(self, value: float) -> None:
        """
        Sets the RasterizationDpi property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            ImageSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeImageSettingsSetRasterizationDpiSingle(self._handle, value)
        self._check_error()

    def get_export_format(self) -> Any:
        """
        Gets the ExportFormat property.

        Returns:
            Any: The value of the ExportFormat property.

        Raises:
            ImageSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeImageSettingsGetExportFormat(self._handle)
        self._check_error()
        return result

    def set_export_format(self, value: Any) -> None:
        """
        Sets the ExportFormat property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            ImageSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeImageSettingsSetExportFormatImageExportFormat(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    @property
    def mode(self) -> Any:
        """
        Gets the Mode property.

        Returns:
            Any: The value of the Mode property.
        """
        return self.get_mode()

    @mode.setter
    def mode(self, value: Any) -> None:
        """
        Sets the mode.

        Args:
            value (Any): The value to set.
        """
        self.set_mode(value)

    @property
    def rasterization_dpi(self) -> float:
        """
        Gets the RasterizationDpi property.

        Returns:
            float: The value of the RasterizationDpi property.
        """
        return self.get_rasterization_dpi()

    @rasterization_dpi.setter
    def rasterization_dpi(self, value: float) -> None:
        """
        Sets the rasterization dpi.

        Args:
            value (float): The value to set.
        """
        self.set_rasterization_dpi(value)

    @property
    def export_format(self) -> Any:
        """
        Gets the ExportFormat property.

        Returns:
            Any: The value of the ExportFormat property.
        """
        return self.get_export_format()

    @export_format.setter
    def export_format(self, value: Any) -> None:
        """
        Sets the export format.

        Args:
            value (Any): The value to set.
        """
        self.set_export_format(value)



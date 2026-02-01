"""
CadSettings module.
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


class CadSettingsError(Exception):
    """Exception raised by CadSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeCadSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeCadSettingsGetLastErrorCode.argtypes = []

_lib.BridgeCadSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeCadSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeCadSettingsFreeErrorString.restype = None
_lib.BridgeCadSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeCadSettingsGetEnableLineWeight.restype = ctypes.c_bool
_lib.BridgeCadSettingsGetEnableLineWeight.argtypes = [ctypes.c_void_p]

_lib.BridgeCadSettingsSetEnableLineWeightBoolean.restype = None
_lib.BridgeCadSettingsSetEnableLineWeightBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeCadSettingsGetCanvasBackgroundColor.restype = ctypes.c_void_p
_lib.BridgeCadSettingsGetCanvasBackgroundColor.argtypes = [ctypes.c_void_p]

_lib.BridgeCadSettingsSetCanvasBackgroundColorColor.restype = None
_lib.BridgeCadSettingsSetCanvasBackgroundColorColor.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeCadSettingsGetRenderingLayoutMode.restype = ctypes.c_int32
_lib.BridgeCadSettingsGetRenderingLayoutMode.argtypes = [ctypes.c_void_p]

_lib.BridgeCadSettingsSetRenderingLayoutModeRenderingLayoutMode.restype = None
_lib.BridgeCadSettingsSetRenderingLayoutModeRenderingLayoutMode.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeCadSettingsGetThumbnailMode.restype = ctypes.c_bool
_lib.BridgeCadSettingsGetThumbnailMode.argtypes = [ctypes.c_void_p]

_lib.BridgeCadSettingsSetThumbnailModeBoolean.restype = None
_lib.BridgeCadSettingsSetThumbnailModeBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeCadSettingsGetUnitMode.restype = ctypes.c_int32
_lib.BridgeCadSettingsGetUnitMode.argtypes = [ctypes.c_void_p]

_lib.BridgeCadSettingsSetUnitModeUnitMode.restype = None
_lib.BridgeCadSettingsSetUnitModeUnitMode.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeCadSettingsGetRenderZoom.restype = ctypes.c_double
_lib.BridgeCadSettingsGetRenderZoom.argtypes = [ctypes.c_void_p]

_lib.BridgeCadSettingsSetRenderZoomDouble.restype = None
_lib.BridgeCadSettingsSetRenderZoomDouble.argtypes = [ctypes.c_void_p, ctypes.c_double]


class CadSettings:
    """
    Merged view of CadSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate CadSettings directly. Use static factory methods instead."""
        raise TypeError("CadSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeCadSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeCadSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeCadSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise CadSettingsError(f"CadSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("CadSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_enable_line_weight(self) -> bool:
        """
        Gets the EnableLineWeight property.

        Returns:
            bool: The value of the EnableLineWeight property.

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeCadSettingsGetEnableLineWeight(self._handle)
        self._check_error()
        return result

    def set_enable_line_weight(self, value: bool) -> None:
        """
        Sets the EnableLineWeight property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeCadSettingsSetEnableLineWeightBoolean(self._handle, value)
        self._check_error()

    def get_canvas_background_color(self) -> 'Color':
        """
        Gets the CanvasBackgroundColor property.

        Returns:
            'Color': The value of the CanvasBackgroundColor property.

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeCadSettingsGetCanvasBackgroundColor(self._handle)
        self._check_error()
        return import_module('.color', package=__package__).Color._from_handle(result)

    def set_canvas_background_color(self, value: 'Color') -> None:
        """
        Sets the CanvasBackgroundColor property.

        Args:
            value ('Color')

        Returns:
            None: The result of the operation

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeCadSettingsSetCanvasBackgroundColorColor(self._handle, value._handle if value else None)
        self._check_error()

    def get_rendering_layout_mode(self) -> Any:
        """
        Gets the RenderingLayoutMode property.

        Returns:
            Any: The value of the RenderingLayoutMode property.

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeCadSettingsGetRenderingLayoutMode(self._handle)
        self._check_error()
        return result

    def set_rendering_layout_mode(self, value: Any) -> None:
        """
        Sets the RenderingLayoutMode property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeCadSettingsSetRenderingLayoutModeRenderingLayoutMode(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_thumbnail_mode(self) -> bool:
        """
        Gets the ThumbnailMode property.

        Returns:
            bool: The value of the ThumbnailMode property.

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeCadSettingsGetThumbnailMode(self._handle)
        self._check_error()
        return result

    def set_thumbnail_mode(self, value: bool) -> None:
        """
        Sets the ThumbnailMode property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeCadSettingsSetThumbnailModeBoolean(self._handle, value)
        self._check_error()

    def get_unit_mode(self) -> Any:
        """
        Gets the UnitMode property.

        Returns:
            Any: The value of the UnitMode property.

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeCadSettingsGetUnitMode(self._handle)
        self._check_error()
        return result

    def set_unit_mode(self, value: Any) -> None:
        """
        Sets the UnitMode property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeCadSettingsSetUnitModeUnitMode(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_render_zoom(self) -> float:
        """
        Gets the RenderZoom property.

        Returns:
            float: The value of the RenderZoom property.

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeCadSettingsGetRenderZoom(self._handle)
        self._check_error()
        return result

    def set_render_zoom(self, value: float) -> None:
        """
        Sets the RenderZoom property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            CadSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeCadSettingsSetRenderZoomDouble(self._handle, value)
        self._check_error()

    @property
    def enable_line_weight(self) -> bool:
        """
        Gets the EnableLineWeight property.

        Returns:
            bool: The value of the EnableLineWeight property.
        """
        return self.get_enable_line_weight()

    @enable_line_weight.setter
    def enable_line_weight(self, value: bool) -> None:
        """
        Sets the enable line weight.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_line_weight(value)

    @property
    def canvas_background_color(self) -> 'Color':
        """
        Gets the CanvasBackgroundColor property.

        Returns:
            'Color': The value of the CanvasBackgroundColor property.
        """
        return self.get_canvas_background_color()

    @canvas_background_color.setter
    def canvas_background_color(self, value: 'Color') -> None:
        """
        Sets the canvas background color.

        Args:
            value ('Color'): The value to set.
        """
        self.set_canvas_background_color(value)

    @property
    def rendering_layout_mode(self) -> Any:
        """
        Gets the RenderingLayoutMode property.

        Returns:
            Any: The value of the RenderingLayoutMode property.
        """
        return self.get_rendering_layout_mode()

    @rendering_layout_mode.setter
    def rendering_layout_mode(self, value: Any) -> None:
        """
        Sets the rendering layout mode.

        Args:
            value (Any): The value to set.
        """
        self.set_rendering_layout_mode(value)

    @property
    def thumbnail_mode(self) -> bool:
        """
        Gets the ThumbnailMode property.

        Returns:
            bool: The value of the ThumbnailMode property.
        """
        return self.get_thumbnail_mode()

    @thumbnail_mode.setter
    def thumbnail_mode(self, value: bool) -> None:
        """
        Sets the thumbnail mode.

        Args:
            value (bool): The value to set.
        """
        self.set_thumbnail_mode(value)

    @property
    def unit_mode(self) -> Any:
        """
        Gets the UnitMode property.

        Returns:
            Any: The value of the UnitMode property.
        """
        return self.get_unit_mode()

    @unit_mode.setter
    def unit_mode(self, value: Any) -> None:
        """
        Sets the unit mode.

        Args:
            value (Any): The value to set.
        """
        self.set_unit_mode(value)

    @property
    def render_zoom(self) -> float:
        """
        Gets the RenderZoom property.

        Returns:
            float: The value of the RenderZoom property.
        """
        return self.get_render_zoom()

    @render_zoom.setter
    def render_zoom(self, value: float) -> None:
        """
        Sets the render zoom.

        Args:
            value (float): The value to set.
        """
        self.set_render_zoom(value)



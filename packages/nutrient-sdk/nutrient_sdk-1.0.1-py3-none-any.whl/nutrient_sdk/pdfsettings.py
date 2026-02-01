"""
PdfSettings module.
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


class PdfSettingsError(Exception):
    """Exception raised by PdfSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfSettingsGetLastErrorCode.argtypes = []

_lib.BridgePdfSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfSettingsGetLastErrorMessage.argtypes = []

_lib.BridgePdfSettingsFreeErrorString.restype = None
_lib.BridgePdfSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsGetConformance.restype = ctypes.c_int32
_lib.BridgePdfSettingsGetConformance.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetConformancePdfConformance.restype = None
_lib.BridgePdfSettingsSetConformancePdfConformance.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfSettingsGetMode.restype = ctypes.c_int32
_lib.BridgePdfSettingsGetMode.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetModePdfSettingsMode.restype = None
_lib.BridgePdfSettingsSetModePdfSettingsMode.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfSettingsGetSavePreferences.restype = ctypes.c_int32
_lib.BridgePdfSettingsGetSavePreferences.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetSavePreferencesPdfSavePreferences.restype = None
_lib.BridgePdfSettingsSetSavePreferencesPdfSavePreferences.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfSettingsGetBitonalImageCompression.restype = ctypes.c_int32
_lib.BridgePdfSettingsGetBitonalImageCompression.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetBitonalImageCompressionPdfCompression.restype = None
_lib.BridgePdfSettingsSetBitonalImageCompressionPdfCompression.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfSettingsGetColorImageCompression.restype = ctypes.c_int32
_lib.BridgePdfSettingsGetColorImageCompression.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetColorImageCompressionPdfCompression.restype = None
_lib.BridgePdfSettingsSetColorImageCompressionPdfCompression.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfSettingsGetEnableColorDetection.restype = ctypes.c_bool
_lib.BridgePdfSettingsGetEnableColorDetection.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetEnableColorDetectionBoolean.restype = None
_lib.BridgePdfSettingsSetEnableColorDetectionBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgePdfSettingsGetUseDeflateOnJpeg.restype = ctypes.c_bool
_lib.BridgePdfSettingsGetUseDeflateOnJpeg.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetUseDeflateOnJpegBoolean.restype = None
_lib.BridgePdfSettingsSetUseDeflateOnJpegBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgePdfSettingsGetZlibLevel.restype = ctypes.c_int32
_lib.BridgePdfSettingsGetZlibLevel.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetZlibLevelInt32.restype = None
_lib.BridgePdfSettingsSetZlibLevelInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfSettingsGetEnableLinearization.restype = ctypes.c_bool
_lib.BridgePdfSettingsGetEnableLinearization.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetEnableLinearizationBoolean.restype = None
_lib.BridgePdfSettingsSetEnableLinearizationBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgePdfSettingsGetOptimize.restype = ctypes.c_bool
_lib.BridgePdfSettingsGetOptimize.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetOptimizeBoolean.restype = None
_lib.BridgePdfSettingsSetOptimizeBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgePdfSettingsGetForceImageDpi.restype = ctypes.c_int32
_lib.BridgePdfSettingsGetForceImageDpi.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSettingsSetForceImageDpiInt32.restype = None
_lib.BridgePdfSettingsSetForceImageDpiInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class PdfSettings:
    """
    Merged view of PdfSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate PdfSettings directly. Use static factory methods instead."""
        raise TypeError("PdfSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfSettingsError(f"PdfSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_conformance(self) -> Any:
        """
        Gets the Conformance property.

        Returns:
            Any: The value of the Conformance property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetConformance(self._handle)
        self._check_error()
        return result

    def set_conformance(self, value: Any) -> None:
        """
        Sets the Conformance property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetConformancePdfConformance(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_mode(self) -> Any:
        """
        Gets the Mode property.

        Returns:
            Any: The value of the Mode property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetMode(self._handle)
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
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetModePdfSettingsMode(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_save_preferences(self) -> Any:
        """
        Gets the SavePreferences property.

        Returns:
            Any: The value of the SavePreferences property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetSavePreferences(self._handle)
        self._check_error()
        return result

    def set_save_preferences(self, value: Any) -> None:
        """
        Sets the SavePreferences property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetSavePreferencesPdfSavePreferences(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_bitonal_image_compression(self) -> Any:
        """
        Gets the BitonalImageCompression property.

        Returns:
            Any: The value of the BitonalImageCompression property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetBitonalImageCompression(self._handle)
        self._check_error()
        return result

    def set_bitonal_image_compression(self, value: Any) -> None:
        """
        Sets the BitonalImageCompression property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetBitonalImageCompressionPdfCompression(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_color_image_compression(self) -> Any:
        """
        Gets the ColorImageCompression property.

        Returns:
            Any: The value of the ColorImageCompression property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetColorImageCompression(self._handle)
        self._check_error()
        return result

    def set_color_image_compression(self, value: Any) -> None:
        """
        Sets the ColorImageCompression property.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetColorImageCompressionPdfCompression(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_enable_color_detection(self) -> bool:
        """
        Gets the EnableColorDetection property.

        Returns:
            bool: The value of the EnableColorDetection property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetEnableColorDetection(self._handle)
        self._check_error()
        return result

    def set_enable_color_detection(self, value: bool) -> None:
        """
        Sets the EnableColorDetection property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetEnableColorDetectionBoolean(self._handle, value)
        self._check_error()

    def get_use_deflate_on_jpeg(self) -> bool:
        """
        Gets the UseDeflateOnJpeg property.

        Returns:
            bool: The value of the UseDeflateOnJpeg property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetUseDeflateOnJpeg(self._handle)
        self._check_error()
        return result

    def set_use_deflate_on_jpeg(self, value: bool) -> None:
        """
        Sets the UseDeflateOnJpeg property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetUseDeflateOnJpegBoolean(self._handle, value)
        self._check_error()

    def get_zlib_level(self) -> int:
        """
        Gets the ZlibLevel property.

        Returns:
            int: The value of the ZlibLevel property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetZlibLevel(self._handle)
        self._check_error()
        return result

    def set_zlib_level(self, value: int) -> None:
        """
        Sets the ZlibLevel property.

        Args:
            value (int)

        Returns:
            None: The result of the operation

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetZlibLevelInt32(self._handle, value)
        self._check_error()

    def get_enable_linearization(self) -> bool:
        """
        Gets the EnableLinearization property.

        Returns:
            bool: The value of the EnableLinearization property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetEnableLinearization(self._handle)
        self._check_error()
        return result

    def set_enable_linearization(self, value: bool) -> None:
        """
        Sets the EnableLinearization property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetEnableLinearizationBoolean(self._handle, value)
        self._check_error()

    def get_optimize(self) -> bool:
        """
        Gets the Optimize property.

        Returns:
            bool: The value of the Optimize property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetOptimize(self._handle)
        self._check_error()
        return result

    def set_optimize(self, value: bool) -> None:
        """
        Sets the Optimize property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetOptimizeBoolean(self._handle, value)
        self._check_error()

    def get_force_image_dpi(self) -> int:
        """
        Gets the ForceImageDpi property.

        Returns:
            int: The value of the ForceImageDpi property.

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSettingsGetForceImageDpi(self._handle)
        self._check_error()
        return result

    def set_force_image_dpi(self, value: int) -> None:
        """
        Sets the ForceImageDpi property.

        Args:
            value (int)

        Returns:
            None: The result of the operation

        Raises:
            PdfSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSettingsSetForceImageDpiInt32(self._handle, value)
        self._check_error()

    @property
    def conformance(self) -> Any:
        """
        Gets the Conformance property.

        Returns:
            Any: The value of the Conformance property.
        """
        return self.get_conformance()

    @conformance.setter
    def conformance(self, value: Any) -> None:
        """
        Sets the conformance.

        Args:
            value (Any): The value to set.
        """
        self.set_conformance(value)

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
    def save_preferences(self) -> Any:
        """
        Gets the SavePreferences property.

        Returns:
            Any: The value of the SavePreferences property.
        """
        return self.get_save_preferences()

    @save_preferences.setter
    def save_preferences(self, value: Any) -> None:
        """
        Sets the save preferences.

        Args:
            value (Any): The value to set.
        """
        self.set_save_preferences(value)

    @property
    def bitonal_image_compression(self) -> Any:
        """
        Gets the BitonalImageCompression property.

        Returns:
            Any: The value of the BitonalImageCompression property.
        """
        return self.get_bitonal_image_compression()

    @bitonal_image_compression.setter
    def bitonal_image_compression(self, value: Any) -> None:
        """
        Sets the bitonal image compression.

        Args:
            value (Any): The value to set.
        """
        self.set_bitonal_image_compression(value)

    @property
    def color_image_compression(self) -> Any:
        """
        Gets the ColorImageCompression property.

        Returns:
            Any: The value of the ColorImageCompression property.
        """
        return self.get_color_image_compression()

    @color_image_compression.setter
    def color_image_compression(self, value: Any) -> None:
        """
        Sets the color image compression.

        Args:
            value (Any): The value to set.
        """
        self.set_color_image_compression(value)

    @property
    def enable_color_detection(self) -> bool:
        """
        Gets the EnableColorDetection property.

        Returns:
            bool: The value of the EnableColorDetection property.
        """
        return self.get_enable_color_detection()

    @enable_color_detection.setter
    def enable_color_detection(self, value: bool) -> None:
        """
        Sets the enable color detection.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_color_detection(value)

    @property
    def use_deflate_on_jpeg(self) -> bool:
        """
        Gets the UseDeflateOnJpeg property.

        Returns:
            bool: The value of the UseDeflateOnJpeg property.
        """
        return self.get_use_deflate_on_jpeg()

    @use_deflate_on_jpeg.setter
    def use_deflate_on_jpeg(self, value: bool) -> None:
        """
        Sets the use deflate on jpeg.

        Args:
            value (bool): The value to set.
        """
        self.set_use_deflate_on_jpeg(value)

    @property
    def zlib_level(self) -> int:
        """
        Gets the ZlibLevel property.

        Returns:
            int: The value of the ZlibLevel property.
        """
        return self.get_zlib_level()

    @zlib_level.setter
    def zlib_level(self, value: int) -> None:
        """
        Sets the zlib level.

        Args:
            value (int): The value to set.
        """
        self.set_zlib_level(value)

    @property
    def enable_linearization(self) -> bool:
        """
        Gets the EnableLinearization property.

        Returns:
            bool: The value of the EnableLinearization property.
        """
        return self.get_enable_linearization()

    @enable_linearization.setter
    def enable_linearization(self, value: bool) -> None:
        """
        Sets the enable linearization.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_linearization(value)

    @property
    def optimize(self) -> bool:
        """
        Gets the Optimize property.

        Returns:
            bool: The value of the Optimize property.
        """
        return self.get_optimize()

    @optimize.setter
    def optimize(self, value: bool) -> None:
        """
        Sets the optimize.

        Args:
            value (bool): The value to set.
        """
        self.set_optimize(value)

    @property
    def force_image_dpi(self) -> int:
        """
        Gets the ForceImageDpi property.

        Returns:
            int: The value of the ForceImageDpi property.
        """
        return self.get_force_image_dpi()

    @force_image_dpi.setter
    def force_image_dpi(self, value: int) -> None:
        """
        Sets the force image dpi.

        Args:
            value (int): The value to set.
        """
        self.set_force_image_dpi(value)



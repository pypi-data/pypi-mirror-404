"""
FinalizerSettings module.
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


class FinalizerSettingsError(Exception):
    """Exception raised by FinalizerSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeFinalizerSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeFinalizerSettingsGetLastErrorCode.argtypes = []

_lib.BridgeFinalizerSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeFinalizerSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeFinalizerSettingsFreeErrorString.restype = None
_lib.BridgeFinalizerSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeFinalizerSettingsGetEnableValidation.restype = ctypes.c_bool
_lib.BridgeFinalizerSettingsGetEnableValidation.argtypes = [ctypes.c_void_p]

_lib.BridgeFinalizerSettingsSetEnableValidationBoolean.restype = None
_lib.BridgeFinalizerSettingsSetEnableValidationBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeFinalizerSettingsGetMinimumDocumentConfidence.restype = ctypes.c_float
_lib.BridgeFinalizerSettingsGetMinimumDocumentConfidence.argtypes = [ctypes.c_void_p]

_lib.BridgeFinalizerSettingsSetMinimumDocumentConfidenceSingle.restype = None
_lib.BridgeFinalizerSettingsSetMinimumDocumentConfidenceSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeFinalizerSettingsGetEnableDocumentLayouthDump.restype = ctypes.c_bool
_lib.BridgeFinalizerSettingsGetEnableDocumentLayouthDump.argtypes = [ctypes.c_void_p]

_lib.BridgeFinalizerSettingsSetEnableDocumentLayouthDumpBoolean.restype = None
_lib.BridgeFinalizerSettingsSetEnableDocumentLayouthDumpBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeFinalizerSettingsGetDocumentGraphLayoutPath.restype = ctypes.c_void_p
_lib.BridgeFinalizerSettingsGetDocumentGraphLayoutPath.argtypes = [ctypes.c_void_p]

_lib.BridgeFinalizerSettingsSetDocumentGraphLayoutPathString.restype = None
_lib.BridgeFinalizerSettingsSetDocumentGraphLayoutPathString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeFinalizerSettingsGetEnableVisualization.restype = ctypes.c_bool
_lib.BridgeFinalizerSettingsGetEnableVisualization.argtypes = [ctypes.c_void_p]

_lib.BridgeFinalizerSettingsSetEnableVisualizationBoolean.restype = None
_lib.BridgeFinalizerSettingsSetEnableVisualizationBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]


class FinalizerSettings:
    """
    Merged view of FinalizerSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate FinalizerSettings directly. Use static factory methods instead."""
        raise TypeError("FinalizerSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeFinalizerSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeFinalizerSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeFinalizerSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise FinalizerSettingsError(f"FinalizerSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("FinalizerSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_enable_validation(self) -> bool:
        """
        Gets the EnableValidation property.

        Returns:
            bool: The value of the EnableValidation property.

        Raises:
            FinalizerSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeFinalizerSettingsGetEnableValidation(self._handle)
        self._check_error()
        return result

    def set_enable_validation(self, value: bool) -> None:
        """
        Sets the EnableValidation property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            FinalizerSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeFinalizerSettingsSetEnableValidationBoolean(self._handle, value)
        self._check_error()

    def get_minimum_document_confidence(self) -> float:
        """
        Gets the MinimumDocumentConfidence property.

        Returns:
            float: The value of the MinimumDocumentConfidence property.

        Raises:
            FinalizerSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeFinalizerSettingsGetMinimumDocumentConfidence(self._handle)
        self._check_error()
        return result

    def set_minimum_document_confidence(self, value: float) -> None:
        """
        Sets the MinimumDocumentConfidence property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            FinalizerSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeFinalizerSettingsSetMinimumDocumentConfidenceSingle(self._handle, value)
        self._check_error()

    def get_enable_document_layouth_dump(self) -> bool:
        """
        Gets the EnableDocumentLayouthDump property.

        Returns:
            bool: The value of the EnableDocumentLayouthDump property.

        Raises:
            FinalizerSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeFinalizerSettingsGetEnableDocumentLayouthDump(self._handle)
        self._check_error()
        return result

    def set_enable_document_layouth_dump(self, value: bool) -> None:
        """
        Sets the EnableDocumentLayouthDump property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            FinalizerSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeFinalizerSettingsSetEnableDocumentLayouthDumpBoolean(self._handle, value)
        self._check_error()

    def get_document_graph_layout_path(self) -> str:
        """
        Gets the DocumentGraphLayoutPath property.

        Returns:
            str: The value of the DocumentGraphLayoutPath property.

        Raises:
            FinalizerSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeFinalizerSettingsGetDocumentGraphLayoutPath(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_document_graph_layout_path(self, value: str) -> None:
        """
        Sets the DocumentGraphLayoutPath property.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            FinalizerSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeFinalizerSettingsSetDocumentGraphLayoutPathString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_enable_visualization(self) -> bool:
        """
        Gets the EnableVisualization property.

        Returns:
            bool: The value of the EnableVisualization property.

        Raises:
            FinalizerSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeFinalizerSettingsGetEnableVisualization(self._handle)
        self._check_error()
        return result

    def set_enable_visualization(self, value: bool) -> None:
        """
        Sets the EnableVisualization property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            FinalizerSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeFinalizerSettingsSetEnableVisualizationBoolean(self._handle, value)
        self._check_error()

    @property
    def enable_validation(self) -> bool:
        """
        Gets the EnableValidation property.

        Returns:
            bool: The value of the EnableValidation property.
        """
        return self.get_enable_validation()

    @enable_validation.setter
    def enable_validation(self, value: bool) -> None:
        """
        Sets the enable validation.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_validation(value)

    @property
    def minimum_document_confidence(self) -> float:
        """
        Gets the MinimumDocumentConfidence property.

        Returns:
            float: The value of the MinimumDocumentConfidence property.
        """
        return self.get_minimum_document_confidence()

    @minimum_document_confidence.setter
    def minimum_document_confidence(self, value: float) -> None:
        """
        Sets the minimum document confidence.

        Args:
            value (float): The value to set.
        """
        self.set_minimum_document_confidence(value)

    @property
    def enable_document_layouth_dump(self) -> bool:
        """
        Gets the EnableDocumentLayouthDump property.

        Returns:
            bool: The value of the EnableDocumentLayouthDump property.
        """
        return self.get_enable_document_layouth_dump()

    @enable_document_layouth_dump.setter
    def enable_document_layouth_dump(self, value: bool) -> None:
        """
        Sets the enable document layouth dump.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_document_layouth_dump(value)

    @property
    def document_graph_layout_path(self) -> str:
        """
        Gets the DocumentGraphLayoutPath property.

        Returns:
            str: The value of the DocumentGraphLayoutPath property.
        """
        return self.get_document_graph_layout_path()

    @document_graph_layout_path.setter
    def document_graph_layout_path(self, value: str) -> None:
        """
        Sets the document graph layout path.

        Args:
            value (str): The value to set.
        """
        self.set_document_graph_layout_path(value)

    @property
    def enable_visualization(self) -> bool:
        """
        Gets the EnableVisualization property.

        Returns:
            bool: The value of the EnableVisualization property.
        """
        return self.get_enable_visualization()

    @enable_visualization.setter
    def enable_visualization(self, value: bool) -> None:
        """
        Sets the enable visualization.

        Args:
            value (bool): The value to set.
        """
        self.set_enable_visualization(value)



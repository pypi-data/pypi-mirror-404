"""
Vision module.
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


class VisionError(Exception):
    """Exception raised by Vision operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeVisionGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeVisionGetLastErrorCode.argtypes = []

_lib.BridgeVisionGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeVisionGetLastErrorMessage.argtypes = []

_lib.BridgeVisionFreeErrorString.restype = None
_lib.BridgeVisionFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionSetDocument.restype = ctypes.c_void_p
_lib.BridgeVisionSetDocument.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionWarmup.restype = None
_lib.BridgeVisionWarmup.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionDescribe.restype = ctypes.c_void_p
_lib.BridgeVisionDescribe.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionExtractContent.restype = ctypes.c_void_p
_lib.BridgeVisionExtractContent.argtypes = [ctypes.c_void_p]

_lib.BridgeVisionExtractContentDocumentLayoutJsonExportSettings.restype = ctypes.c_void_p
_lib.BridgeVisionExtractContentDocumentLayoutJsonExportSettings.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeVisionExtractContentToFileString.restype = None
_lib.BridgeVisionExtractContentToFileString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeVisionExtractContentToFileStringDocumentLayoutJsonExportSettings.restype = None
_lib.BridgeVisionExtractContentToFileStringDocumentLayoutJsonExportSettings.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]


class Vision:
    """
    Provides machine learning and computer vision capabilities for document processing. Enables AI-powered document description and content extraction.
    """

    def __init__(self):
        """Cannot instantiate Vision directly. Use static factory methods instead."""
        raise TypeError("Vision cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeVisionGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeVisionGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeVisionFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise VisionError(f"Vision: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("Vision instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    @classmethod
    def set(cls, document: 'Document') -> 'Vision':
        """
        Creates a Vision instance for the specified document.

        Args:
            document ('Document')

        Returns:
            'Vision': A Vision instance ready to perform analysis on the document.

        Raises:
            VisionError: If the operation fails
        """

        result = _lib.BridgeVisionSetDocument(document._handle if document else None)
        error_code = _lib.BridgeVisionGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeVisionGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeVisionFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise VisionError(f"Set: {message} (code: {error_code})")
        return import_module('.vision', package=__package__).Vision._from_handle(result)

    def warmup(self) -> None:
        """
        Preloads (warms up) all resources needed for vision processing. This downloads all model files based on the document's VisionSettings before execution. Call this to avoid download delays during ExtractContent().

        Returns:
            None: The result of the operation

        Raises:
            VisionError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeVisionWarmup(self._handle)
        self._check_error()

    def describe(self) -> str:
        """
        Generates an AI-powered description of the document content.

        Returns:
            str: A string containing the document description.

        Raises:
            VisionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeVisionDescribe(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def extract_content(self, settings: Optional['DocumentLayoutJsonExportSettings'] = None) -> str:
        """
        Extracts structured content from the document using machine vision processing. The pipeline used is determined by the setting.

        This method has multiple overloads. Arguments are resolved at runtime.

        Raises:
            VisionError: If the operation fails
            TypeError: If no matching overload is found
        """
        self._ensure_not_closed()

        _args = (settings,)
        _overload_map = {
            (): 'BridgeVisionExtractContent',
            ('DocumentLayoutJsonExportSettings',): 'BridgeVisionExtractContentDocumentLayoutJsonExportSettings',
        }

        _bridge_func_name = sdk_helpers.resolve_overload(_overload_map, *_args)
        if _bridge_func_name is None:
            raise TypeError(sdk_helpers.format_overload_error('extract_content', _overload_map, *_args))

        _bridge_func = getattr(_lib, _bridge_func_name)
        _call_args = [self._handle]
        _nullable_indices = set()
        for _idx, _arg in enumerate(_args):
            if _idx in _nullable_indices:
                # Nullable parameter: pass value (or 0 if None) and hasValue boolean
                if _arg is not None and hasattr(_arg, '_handle'):
                    _call_args.append(_arg._handle)
                else:
                    _call_args.append(_arg if _arg is not None else 0)
                _call_args.append(_arg is not None)
            elif _arg is not None:
                if isinstance(_arg, str):
                    _call_args.append(_arg.encode('utf-8'))
                elif hasattr(_arg, '_handle'):
                    _call_args.append(_arg._handle)
                elif isinstance(_arg, Enum):
                    _call_args.append(_arg.value)
                else:
                    _call_args.append(_arg)

        result = _bridge_func(*_call_args)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def extract_content_to_file(self, output_path: str, settings: Optional['DocumentLayoutJsonExportSettings'] = None) -> None:
        """
        Extracts structured content from the document and saves it to a JSON file. Uses the document's DocumentLayoutJsonExportSettings for configuration.

        This method has multiple overloads. Arguments are resolved at runtime.

        Raises:
            VisionError: If the operation fails
            TypeError: If no matching overload is found
        """
        self._ensure_not_closed()

        _args = (output_path, settings)
        _overload_map = {
            ('str',): 'BridgeVisionExtractContentToFileString',
            ('str', 'DocumentLayoutJsonExportSettings'): 'BridgeVisionExtractContentToFileStringDocumentLayoutJsonExportSettings',
        }

        _bridge_func_name = sdk_helpers.resolve_overload(_overload_map, *_args)
        if _bridge_func_name is None:
            raise TypeError(sdk_helpers.format_overload_error('extract_content_to_file', _overload_map, *_args))

        _bridge_func = getattr(_lib, _bridge_func_name)
        _call_args = [self._handle]
        _nullable_indices = set()
        for _idx, _arg in enumerate(_args):
            if _idx in _nullable_indices:
                # Nullable parameter: pass value (or 0 if None) and hasValue boolean
                if _arg is not None and hasattr(_arg, '_handle'):
                    _call_args.append(_arg._handle)
                else:
                    _call_args.append(_arg if _arg is not None else 0)
                _call_args.append(_arg is not None)
            elif _arg is not None:
                if isinstance(_arg, str):
                    _call_args.append(_arg.encode('utf-8'))
                elif hasattr(_arg, '_handle'):
                    _call_args.append(_arg._handle)
                elif isinstance(_arg, Enum):
                    _call_args.append(_arg.value)
                else:
                    _call_args.append(_arg)

        _bridge_func(*_call_args)
        self._check_error()



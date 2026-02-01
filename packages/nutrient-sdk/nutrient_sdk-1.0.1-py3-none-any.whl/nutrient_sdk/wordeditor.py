"""
WordEditor module.
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


class WordEditorError(Exception):
    """Exception raised by WordEditor operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeWordEditorGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeWordEditorGetLastErrorCode.argtypes = []

_lib.BridgeWordEditorGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeWordEditorGetLastErrorMessage.argtypes = []

_lib.BridgeWordEditorFreeErrorString.restype = None
_lib.BridgeWordEditorFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeWordEditorEditDocument.restype = ctypes.c_void_p
_lib.BridgeWordEditorEditDocument.argtypes = [ctypes.c_void_p]

_lib.BridgeWordEditorSave.restype = None
_lib.BridgeWordEditorSave.argtypes = [ctypes.c_void_p]

_lib.BridgeWordEditorSaveAsString.restype = None
_lib.BridgeWordEditorSaveAsString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeWordEditorClose.restype = None
_lib.BridgeWordEditorClose.argtypes = [ctypes.c_void_p]

_lib.BridgeWordEditorApplyTemplateModelString.restype = None
_lib.BridgeWordEditorApplyTemplateModelString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeWordEditorSaveWithModelAsString.restype = None
_lib.BridgeWordEditorSaveWithModelAsString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


class WordEditor:
    """
    Provides specialized editing capabilities for Word documents. Supports template-based document generation and manipulation of OpenXML Word documents.
    """

    def __init__(self):
        """Cannot instantiate WordEditor directly. Use static factory methods instead."""
        raise TypeError("WordEditor cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeWordEditorGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeWordEditorGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeWordEditorFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise WordEditorError(f"WordEditor: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("WordEditor instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    @classmethod
    def edit(cls, document: 'Document') -> 'WordEditor':
        """
        Creates a new WordEditor instance and begins editing the specified document.

        Args:
            document ('Document')

        Returns:
            'WordEditor': A new WordEditor instance for editing the document.

        Raises:
            WordEditorError: If the operation fails
        """

        result = _lib.BridgeWordEditorEditDocument(document._handle if document else None)
        error_code = _lib.BridgeWordEditorGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeWordEditorGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeWordEditorFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise WordEditorError(f"Edit: {message} (code: {error_code})")
        return import_module('.wordeditor', package=__package__).WordEditor._from_handle(result)

    def save(self) -> None:
        """
        Saves the current changes made in the editor.

        Returns:
            None: The result of the operation

        Raises:
            WordEditorError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeWordEditorSave(self._handle)
        self._check_error()

    def save_as(self, path: str) -> None:
        """
        Saves the current changes to a file at the specified path.

        Args:
            path (str)

        Returns:
            None: The result of the operation

        Raises:
            WordEditorError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeWordEditorSaveAsString(self._handle, path.encode('utf-8') if path else None)
        self._check_error()

    def close(self) -> None:
        """
        Closes the editor and releases all associated resources.

        Returns:
            None: The result of the operation

        Raises:
            WordEditorError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeWordEditorClose(self._handle)
        self._check_error()

    def apply_template_model(self, json_template: str) -> None:
        """
        Applies a template model to the Word document from a JSON string.

        Args:
            json_template (str)

        Returns:
            None: The result of the operation

        Raises:
            WordEditorError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeWordEditorApplyTemplateModelString(self._handle, json_template.encode('utf-8') if json_template else None)
        self._check_error()

    def save_with_model_as(self, path: str) -> None:
        """
        Saves the Word document with the applied template model to a file.

        Args:
            path (str)

        Returns:
            None: The result of the operation

        Raises:
            WordEditorError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeWordEditorSaveWithModelAsString(self._handle, path.encode('utf-8') if path else None)
        self._check_error()



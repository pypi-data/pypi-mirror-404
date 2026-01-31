"""
PdfEditor module.
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


class PdfEditorError(Exception):
    """Exception raised by PdfEditor operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfEditorGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfEditorGetLastErrorCode.argtypes = []

_lib.BridgePdfEditorGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfEditorGetLastErrorMessage.argtypes = []

_lib.BridgePdfEditorFreeErrorString.restype = None
_lib.BridgePdfEditorFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfEditorEditDocument.restype = ctypes.c_void_p
_lib.BridgePdfEditorEditDocument.argtypes = [ctypes.c_void_p]

_lib.BridgePdfEditorSave.restype = None
_lib.BridgePdfEditorSave.argtypes = [ctypes.c_void_p]

_lib.BridgePdfEditorSaveAsString.restype = None
_lib.BridgePdfEditorSaveAsString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfEditorClose.restype = None
_lib.BridgePdfEditorClose.argtypes = [ctypes.c_void_p]

_lib.BridgePdfEditorGetPageCollection.restype = ctypes.c_void_p
_lib.BridgePdfEditorGetPageCollection.argtypes = [ctypes.c_void_p]

_lib.BridgePdfEditorGetMetadata.restype = ctypes.c_void_p
_lib.BridgePdfEditorGetMetadata.argtypes = [ctypes.c_void_p]

_lib.BridgePdfEditorGetFormFieldCollection.restype = ctypes.c_void_p
_lib.BridgePdfEditorGetFormFieldCollection.argtypes = [ctypes.c_void_p]

_lib.BridgePdfEditorAppendDocumentDocument.restype = None
_lib.BridgePdfEditorAppendDocumentDocument.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


class PdfEditor:
    """
    Provides specialized editing capabilities for PDF documents. Implements document and page-based editing operations specific to PDF format.
    """

    def __init__(self):
        """Cannot instantiate PdfEditor directly. Use static factory methods instead."""
        raise TypeError("PdfEditor cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfEditorGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfEditorGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfEditorFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfEditorError(f"PdfEditor: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfEditor instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    @classmethod
    def edit(cls, document: 'Document') -> 'PdfEditor':
        """
        Creates a new PdfEditor instance and begins editing the specified document.

        Args:
            document ('Document')

        Returns:
            'PdfEditor': A new PdfEditor instance for editing the document.

        Raises:
            PdfEditorError: If the operation fails
        """

        result = _lib.BridgePdfEditorEditDocument(document._handle if document else None)
        error_code = _lib.BridgePdfEditorGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfEditorGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfEditorFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfEditorError(f"Edit: {message} (code: {error_code})")
        return import_module('.pdfeditor', package=__package__).PdfEditor._from_handle(result)

    def save(self) -> None:
        """
        Saves the current changes made in the editor.

        Returns:
            None: The result of the operation

        Raises:
            PdfEditorError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfEditorSave(self._handle)
        self._check_error()

    def save_as(self, path: str) -> None:
        """
        Saves the current changes to a file at the specified path.

        Args:
            path (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfEditorError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfEditorSaveAsString(self._handle, path.encode('utf-8') if path else None)
        self._check_error()

    def close(self) -> None:
        """
        Closes the editor and releases all associated resources.

        Returns:
            None: The result of the operation

        Raises:
            PdfEditorError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfEditorClose(self._handle)
        self._check_error()

    def get_page_collection(self) -> 'PdfPageCollection':
        """
        Gets the collection of pages in the PDF document.

        Returns:
            'PdfPageCollection': The value of the PageCollection property.

        Raises:
            PdfEditorError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfEditorGetPageCollection(self._handle)
        self._check_error()
        return import_module('.pdfpagecollection', package=__package__).PdfPageCollection._from_handle(result)

    def get_metadata(self) -> 'PdfMetadata':
        """
        Gets the metadata associated with the current PDF document.

        Returns:
            'PdfMetadata': The value of the Metadata property.

        Raises:
            PdfEditorError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfEditorGetMetadata(self._handle)
        self._check_error()
        return import_module('.pdfmetadata', package=__package__).PdfMetadata._from_handle(result)

    def get_form_field_collection(self) -> 'PdfFormFieldCollection':
        """
        Gets the collection of form fields in the PDF document.

        Returns:
            'PdfFormFieldCollection': The value of the FormFieldCollection property.

        Raises:
            PdfEditorError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfEditorGetFormFieldCollection(self._handle)
        self._check_error()
        return import_module('.pdfformfieldcollection', package=__package__).PdfFormFieldCollection._from_handle(result)

    def append_document(self, document: 'Document') -> None:
        """
        Appends all pages from another document to the end of the current PDF document.

        Args:
            document ('Document')

        Returns:
            None: The result of the operation

        Raises:
            PdfEditorError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfEditorAppendDocumentDocument(self._handle, document._handle if document else None)
        self._check_error()

    @property
    def page_collection(self) -> 'PdfPageCollection':
        """
        Gets the collection of pages in the PDF document.

        Returns:
            'PdfPageCollection': The value of the PageCollection property.
        """
        return self.get_page_collection()

    @property
    def metadata(self) -> 'PdfMetadata':
        """
        Gets the metadata associated with the current PDF document.

        Returns:
            'PdfMetadata': The value of the Metadata property.
        """
        return self.get_metadata()

    @property
    def form_field_collection(self) -> 'PdfFormFieldCollection':
        """
        Gets the collection of form fields in the PDF document.

        Returns:
            'PdfFormFieldCollection': The value of the FormFieldCollection property.
        """
        return self.get_form_field_collection()



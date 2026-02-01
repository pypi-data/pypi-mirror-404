"""
PdfPage module.
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


class PdfPageError(Exception):
    """Exception raised by PdfPage operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfPageGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfPageGetLastErrorCode.argtypes = []

_lib.BridgePdfPageGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfPageGetLastErrorMessage.argtypes = []

_lib.BridgePdfPageFreeErrorString.restype = None
_lib.BridgePdfPageFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageGetPageNumber.restype = ctypes.c_int32
_lib.BridgePdfPageGetPageNumber.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageGetWidth.restype = ctypes.c_float
_lib.BridgePdfPageGetWidth.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageGetHeight.restype = ctypes.c_float
_lib.BridgePdfPageGetHeight.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageGetRotation.restype = ctypes.c_int32
_lib.BridgePdfPageGetRotation.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageGetAnnotationCollection.restype = ctypes.c_void_p
_lib.BridgePdfPageGetAnnotationCollection.argtypes = [ctypes.c_void_p]


class PdfPage:
    """
    Represents a page in a PDF document with size, positioning, and annotation capabilities. This class provides functionality to manage page dimensions, boxes, rotation, and annotations.
    """

    def __init__(self):
        """Cannot instantiate PdfPage directly. Use static factory methods instead."""
        raise TypeError("PdfPage cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfPageGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfPageGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfPageFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfPageError(f"PdfPage: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfPage instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_page_number(self) -> int:
        """
        Gets the 1-based page number of this page in the document.

        Returns:
            int: The value of the PageNumber property.

        Raises:
            PdfPageError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageGetPageNumber(self._handle)
        self._check_error()
        return result

    def get_width(self) -> float:
        """
        Gets the width of the page in points.

        Returns:
            float: The value of the Width property.

        Raises:
            PdfPageError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageGetWidth(self._handle)
        self._check_error()
        return result

    def get_height(self) -> float:
        """
        Gets the height of the page in points.

        Returns:
            float: The value of the Height property.

        Raises:
            PdfPageError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageGetHeight(self._handle)
        self._check_error()
        return result

    def get_rotation(self) -> int:
        """
        Gets the rotation of the page in degrees (0, 90, 180, or 270).

        Returns:
            int: The value of the Rotation property.

        Raises:
            PdfPageError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageGetRotation(self._handle)
        self._check_error()
        return result

    def get_annotation_collection(self) -> 'PdfAnnotationCollection':
        """
        Gets the collection of annotations on this page.

        Returns:
            'PdfAnnotationCollection': The value of the AnnotationCollection property.

        Raises:
            PdfPageError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageGetAnnotationCollection(self._handle)
        self._check_error()
        return import_module('.pdfannotationcollection', package=__package__).PdfAnnotationCollection._from_handle(result)

    @property
    def page_number(self) -> int:
        """
        Gets the 1-based page number of this page in the document.

        Returns:
            int: The value of the PageNumber property.
        """
        return self.get_page_number()

    @property
    def width(self) -> float:
        """
        Gets the width of the page in points.

        Returns:
            float: The value of the Width property.
        """
        return self.get_width()

    @property
    def height(self) -> float:
        """
        Gets the height of the page in points.

        Returns:
            float: The value of the Height property.
        """
        return self.get_height()

    @property
    def rotation(self) -> int:
        """
        Gets the rotation of the page in degrees (0, 90, 180, or 270).

        Returns:
            int: The value of the Rotation property.
        """
        return self.get_rotation()

    @property
    def annotation_collection(self) -> 'PdfAnnotationCollection':
        """
        Gets the collection of annotations on this page.

        Returns:
            'PdfAnnotationCollection': The value of the AnnotationCollection property.
        """
        return self.get_annotation_collection()



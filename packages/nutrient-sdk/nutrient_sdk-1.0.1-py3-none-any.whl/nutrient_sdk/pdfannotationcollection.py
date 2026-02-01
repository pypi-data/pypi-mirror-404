"""
PdfAnnotationCollection module.
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


class PdfAnnotationCollectionError(Exception):
    """Exception raised by PdfAnnotationCollection operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfAnnotationCollectionGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfAnnotationCollectionGetLastErrorCode.argtypes = []

_lib.BridgePdfAnnotationCollectionGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionGetLastErrorMessage.argtypes = []

_lib.BridgePdfAnnotationCollectionFreeErrorString.restype = None
_lib.BridgePdfAnnotationCollectionFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionGetItemInt32.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionGetItemInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfAnnotationCollectionGetEnumerator.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionGetEnumerator.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionGetCount.restype = ctypes.c_int32
_lib.BridgePdfAnnotationCollectionGetCount.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionGetItemInt32.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionGetItemInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfAnnotationCollectionAddStickyNoteSingleSingleStringStringString.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddStickyNoteSingleSingleStringStringString.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionAddHighlightSingleSingleSingleSingleStringString.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddHighlightSingleSingleSingleSingleStringString.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionAddUnderlineSingleSingleSingleSingleStringString.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddUnderlineSingleSingleSingleSingleStringString.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionAddStrikeOutSingleSingleSingleSingleStringString.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddStrikeOutSingleSingleSingleSingleStringString.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionAddSquigglySingleSingleSingleSingleStringString.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddSquigglySingleSingleSingleSingleStringString.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionAddStampSingleSingleSingleSingleStringString.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddStampSingleSingleSingleSingleStringString.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionAddLinkSingleSingleSingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddLinkSingleSingleSingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]

_lib.BridgePdfAnnotationCollectionRemoveAtInt32.restype = None
_lib.BridgePdfAnnotationCollectionRemoveAtInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfAnnotationCollectionAddLineSingleSingleSingleSingleStringString.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddLineSingleSingleSingleSingleStringString.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionAddCircleSingleSingleSingleSingleStringString.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddCircleSingleSingleSingleSingleStringString.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionAddSquareSingleSingleSingleSingleStringString.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddSquareSingleSingleSingleSingleStringString.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionAddFreeTextSingleSingleSingleSingleStringStringStringSingleColor.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddFreeTextSingleSingleSingleSingleStringStringStringSingleColor.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_void_p]

_lib.BridgePdfAnnotationCollectionAddRedactSingleSingleSingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationCollectionAddRedactSingleSingleSingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]


class PdfAnnotationCollection:
    """
    Represents a collection of annotations on a PDF page. Provides methods to access, add, and remove annotations.
    """

    def __init__(self):
        """Cannot instantiate PdfAnnotationCollection directly. Use static factory methods instead."""
        raise TypeError("PdfAnnotationCollection cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfAnnotationCollectionGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfAnnotationCollectionGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfAnnotationCollectionFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfAnnotationCollectionError(f"PdfAnnotationCollection: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfAnnotationCollection instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_enumerator(self) -> Any:
        """
        Returns an enumerator that iterates through the annotation's collection.

        Returns:
            Any: An enumerator for the annotation's collection.

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionGetEnumerator(self._handle)
        self._check_error()
        return result

    def get_count(self) -> int:
        """
        Gets the number of annotations in the collection.

        Returns:
            int: The value of the Count property.

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionGetCount(self._handle)
        self._check_error()
        return result

    def get_item(self, index: int) -> 'PdfAnnotation':
        """
        Returns the element at the specified index.

        Args:
            index (int)

        Returns:
            'PdfAnnotation': The element at the specified index.

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionGetItemInt32(self._handle, index)
        self._check_error()
        return self._create_typed_element(result)

    def add_sticky_note(self, x: float, y: float, author: str, subject: str, contents: str) -> 'PdfTextAnnotation':
        """
        Adds a sticky note (text) annotation to this page.

        Args:
            x (float)
            y (float)
            author (str)
            subject (str)
            contents (str)

        Returns:
            'PdfTextAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddStickyNoteSingleSingleStringStringString(self._handle, x, y, author.encode('utf-8') if author else None, subject.encode('utf-8') if subject else None, contents.encode('utf-8') if contents else None)
        self._check_error()
        return import_module('.pdftextannotation', package=__package__).PdfTextAnnotation._from_handle(result)

    def add_highlight(self, x: float, y: float, width: float, height: float, author: str, contents: str) -> 'PdfHighlightAnnotation':
        """
        Adds a highlight annotation to this page.

        Args:
            x (float)
            y (float)
            width (float)
            height (float)
            author (str)
            contents (str)

        Returns:
            'PdfHighlightAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddHighlightSingleSingleSingleSingleStringString(self._handle, x, y, width, height, author.encode('utf-8') if author else None, contents.encode('utf-8') if contents else None)
        self._check_error()
        return import_module('.pdfhighlightannotation', package=__package__).PdfHighlightAnnotation._from_handle(result)

    def add_underline(self, x: float, y: float, width: float, height: float, author: str, contents: str) -> 'PdfUnderlineAnnotation':
        """
        Adds an underline annotation to this page.

        Args:
            x (float)
            y (float)
            width (float)
            height (float)
            author (str)
            contents (str)

        Returns:
            'PdfUnderlineAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddUnderlineSingleSingleSingleSingleStringString(self._handle, x, y, width, height, author.encode('utf-8') if author else None, contents.encode('utf-8') if contents else None)
        self._check_error()
        return import_module('.pdfunderlineannotation', package=__package__).PdfUnderlineAnnotation._from_handle(result)

    def add_strike_out(self, x: float, y: float, width: float, height: float, author: str, contents: str) -> 'PdfStrikeOutAnnotation':
        """
        Adds a strikeout annotation to this page.

        Args:
            x (float)
            y (float)
            width (float)
            height (float)
            author (str)
            contents (str)

        Returns:
            'PdfStrikeOutAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddStrikeOutSingleSingleSingleSingleStringString(self._handle, x, y, width, height, author.encode('utf-8') if author else None, contents.encode('utf-8') if contents else None)
        self._check_error()
        return import_module('.pdfstrikeoutannotation', package=__package__).PdfStrikeOutAnnotation._from_handle(result)

    def add_squiggly(self, x: float, y: float, width: float, height: float, author: str, contents: str) -> 'PdfSquigglyAnnotation':
        """
        Adds a squiggly underline annotation to this page.

        Args:
            x (float)
            y (float)
            width (float)
            height (float)
            author (str)
            contents (str)

        Returns:
            'PdfSquigglyAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddSquigglySingleSingleSingleSingleStringString(self._handle, x, y, width, height, author.encode('utf-8') if author else None, contents.encode('utf-8') if contents else None)
        self._check_error()
        return import_module('.pdfsquigglyannotation', package=__package__).PdfSquigglyAnnotation._from_handle(result)

    def add_stamp(self, x: float, y: float, width: float, height: float, title: str, contents: str) -> 'PdfStampAnnotation':
        """
        Adds a rubber stamp annotation to this page.

        Args:
            x (float)
            y (float)
            width (float)
            height (float)
            title (str)
            contents (str)

        Returns:
            'PdfStampAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddStampSingleSingleSingleSingleStringString(self._handle, x, y, width, height, title.encode('utf-8') if title else None, contents.encode('utf-8') if contents else None)
        self._check_error()
        return import_module('.pdfstampannotation', package=__package__).PdfStampAnnotation._from_handle(result)

    def add_link(self, x: float, y: float, width: float, height: float) -> 'PdfLinkAnnotation':
        """
        Adds an empty link annotation to this page. Use the returned annotation's property or method to configure the link target.

        Args:
            x (float)
            y (float)
            width (float)
            height (float)

        Returns:
            'PdfLinkAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddLinkSingleSingleSingleSingle(self._handle, x, y, width, height)
        self._check_error()
        return import_module('.pdflinkannotation', package=__package__).PdfLinkAnnotation._from_handle(result)

    def remove_at(self, index: int) -> None:
        """
        Removes the annotation at the specified index.

        Args:
            index (int)

        Returns:
            None: The result of the operation

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationCollectionRemoveAtInt32(self._handle, index)
        self._check_error()

    def add_line(self, start_x: float, start_y: float, end_x: float, end_y: float, author: str, contents: str) -> 'PdfLineAnnotation':
        """
        Adds a line annotation to this page.

        Args:
            start_x (float)
            start_y (float)
            end_x (float)
            end_y (float)
            author (str)
            contents (str)

        Returns:
            'PdfLineAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddLineSingleSingleSingleSingleStringString(self._handle, start_x, start_y, end_x, end_y, author.encode('utf-8') if author else None, contents.encode('utf-8') if contents else None)
        self._check_error()
        return import_module('.pdflineannotation', package=__package__).PdfLineAnnotation._from_handle(result)

    def add_circle(self, x: float, y: float, width: float, height: float, author: str, contents: str) -> 'PdfCircleAnnotation':
        """
        Adds a circle (ellipse) annotation to this page.

        Args:
            x (float)
            y (float)
            width (float)
            height (float)
            author (str)
            contents (str)

        Returns:
            'PdfCircleAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddCircleSingleSingleSingleSingleStringString(self._handle, x, y, width, height, author.encode('utf-8') if author else None, contents.encode('utf-8') if contents else None)
        self._check_error()
        return import_module('.pdfcircleannotation', package=__package__).PdfCircleAnnotation._from_handle(result)

    def add_square(self, x: float, y: float, width: float, height: float, author: str, contents: str) -> 'PdfSquareAnnotation':
        """
        Adds a square (rectangle) annotation to this page.

        Args:
            x (float)
            y (float)
            width (float)
            height (float)
            author (str)
            contents (str)

        Returns:
            'PdfSquareAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddSquareSingleSingleSingleSingleStringString(self._handle, x, y, width, height, author.encode('utf-8') if author else None, contents.encode('utf-8') if contents else None)
        self._check_error()
        return import_module('.pdfsquareannotation', package=__package__).PdfSquareAnnotation._from_handle(result)

    def add_free_text(self, x: float, y: float, width: float, height: float, author: str, contents: str, font_name: str, font_size: float, font_color: 'Color') -> 'PdfFreeTextAnnotation':
        """
        Adds a free text annotation (text box) to this page.

        Args:
            x (float)
            y (float)
            width (float)
            height (float)
            author (str)
            contents (str)
            font_name (str)
            font_size (float)
            font_color ('Color')

        Returns:
            'PdfFreeTextAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddFreeTextSingleSingleSingleSingleStringStringStringSingleColor(self._handle, x, y, width, height, author.encode('utf-8') if author else None, contents.encode('utf-8') if contents else None, font_name.encode('utf-8') if font_name else None, font_size, font_color._handle if font_color else None)
        self._check_error()
        return import_module('.pdffreetextannotation', package=__package__).PdfFreeTextAnnotation._from_handle(result)

    def add_redact(self, x: float, y: float, width: float, height: float) -> 'PdfRedactAnnotation':
        """
        Adds a redaction annotation to this page. The annotation marks content for redaction but does not apply the redaction until is called.

        Args:
            x (float)
            y (float)
            width (float)
            height (float)

        Returns:
            'PdfRedactAnnotation': The newly created .

        Raises:
            PdfAnnotationCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationCollectionAddRedactSingleSingleSingleSingle(self._handle, x, y, width, height)
        self._check_error()
        return import_module('.pdfredactannotation', package=__package__).PdfRedactAnnotation._from_handle(result)

    @property
    def enumerator(self) -> Any:
        """
        Returns an enumerator that iterates through the annotation's collection.

        Returns:
            Any: An enumerator for the annotation's collection.
        """
        return self.get_enumerator()

    @property
    def count(self) -> int:
        """
        Gets the number of annotations in the collection.

        Returns:
            int: The value of the Count property.
        """
        return self.get_count()

    # Collection support for iteration
    def __iter__(self):
        """
        Returns an iterator over the elements in this collection.

        Yields:
            PdfAnnotation: Each element in the collection
        """
        for i in range(self.get_count()):
            yield self[i]

    def __len__(self) -> int:
        """
        Returns the number of elements in this collection.

        Returns:
            int: The number of elements
        """
        return self.get_count()

    def __getitem__(self, index: int) -> 'PdfAnnotation':
        """
        Returns the element at the specified position.

        Args:
            index (int): The index of the element to return (0-based)

        Returns:
            PdfAnnotation: The element at the specified position

        Raises:
            IndexError: If the index is out of range
        """
        if index < 0 or index >= self.get_count():
            raise IndexError(f"Index {index} out of range for collection of size {self.get_count()}")
        return self._get_item(index)

    def _create_typed_element(self, handle):
        """
        Creates a properly-typed element instance from a native handle.
        Queries the actual runtime type and returns the correct subclass.
        """
        if not handle:
            return None

        # Query the actual type directly from the handle without creating a wrapper instance
        element_module = import_module('.pdfannotation', package=__package__)
        actual_type = element_module.PdfAnnotation._get_sub_type_from_handle(handle)
        if actual_type is None:
            return element_module.PdfAnnotation._from_handle(handle)

        # Map string discriminator to specific subtype
        type_map = {
            'Text': ('pdftextannotation', 'PdfTextAnnotation'),
            'Highlight': ('pdfhighlightannotation', 'PdfHighlightAnnotation'),
            'Underline': ('pdfunderlineannotation', 'PdfUnderlineAnnotation'),
            'StrikeOut': ('pdfstrikeoutannotation', 'PdfStrikeOutAnnotation'),
            'Squiggly': ('pdfsquigglyannotation', 'PdfSquigglyAnnotation'),
            'Stamp': ('pdfstampannotation', 'PdfStampAnnotation'),
            'Link': ('pdflinkannotation', 'PdfLinkAnnotation'),
            'Line': ('pdflineannotation', 'PdfLineAnnotation'),
            'Circle': ('pdfcircleannotation', 'PdfCircleAnnotation'),
            'Square': ('pdfsquareannotation', 'PdfSquareAnnotation'),
            'FreeText': ('pdffreetextannotation', 'PdfFreeTextAnnotation'),
            'Redact': ('pdfredactannotation', 'PdfRedactAnnotation'),
        }

        if actual_type in type_map:
            module_name, class_name = type_map[actual_type]
            subtype_module = import_module('.' + module_name, package=__package__)
            return getattr(subtype_module, class_name)._from_handle(handle)

        # Default to base type
        return element_module.PdfAnnotation._from_handle(handle)

    def _get_item(self, index: int) -> 'PdfAnnotation':
        """Internal method to get item at index."""
        self._ensure_not_closed()
        result = _lib.BridgePdfAnnotationCollectionGetItemInt32(self._handle, index)
        self._check_error()
        return self._create_typed_element(result)



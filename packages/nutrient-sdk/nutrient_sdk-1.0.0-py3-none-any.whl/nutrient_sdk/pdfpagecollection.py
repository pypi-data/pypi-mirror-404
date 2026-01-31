"""
PdfPageCollection module.
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


class PdfPageCollectionError(Exception):
    """Exception raised by PdfPageCollection operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfPageCollectionGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfPageCollectionGetLastErrorCode.argtypes = []

_lib.BridgePdfPageCollectionGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionGetLastErrorMessage.argtypes = []

_lib.BridgePdfPageCollectionFreeErrorString.restype = None
_lib.BridgePdfPageCollectionFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageCollectionGetItemInt32.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionGetItemInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfPageCollectionAdd.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionAdd.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageCollectionInsertInt32.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionInsertInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfPageCollectionGetEnumerator.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionGetEnumerator.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageCollectionGetCount.restype = ctypes.c_int32
_lib.BridgePdfPageCollectionGetCount.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageCollectionGetFirst.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionGetFirst.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageCollectionGetLast.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionGetLast.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPageCollectionGetItemInt32.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionGetItemInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfPageCollectionGetPageInt32.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionGetPageInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfPageCollectionAddSingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionAddSingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float]

_lib.BridgePdfPageCollectionAddPdfPageSizes.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionAddPdfPageSizes.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfPageCollectionInsertInt32SingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionInsertInt32SingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_float, ctypes.c_float]

_lib.BridgePdfPageCollectionInsertInt32PdfPageSizes.restype = ctypes.c_void_p
_lib.BridgePdfPageCollectionInsertInt32PdfPageSizes.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32]

_lib.BridgePdfPageCollectionRemoveAtInt32.restype = None
_lib.BridgePdfPageCollectionRemoveAtInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfPageCollectionSwapInt32Int32.restype = None
_lib.BridgePdfPageCollectionSwapInt32Int32.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32]

_lib.BridgePdfPageCollectionMoveToInt32Int32.restype = None
_lib.BridgePdfPageCollectionMoveToInt32Int32.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32]


class PdfPageCollection:
    """
    Represents a collection of pages in a PDF document. Provides indexed access to individual objects and methods to manipulate the page structure.
    """

    def __init__(self):
        """Cannot instantiate PdfPageCollection directly. Use static factory methods instead."""
        raise TypeError("PdfPageCollection cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfPageCollectionGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfPageCollectionGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfPageCollectionFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfPageCollectionError(f"PdfPageCollection: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfPageCollection instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def add(self, width: Optional[float] = None, height: Optional[float] = None, page_size: Optional[Any] = None) -> 'PdfPage':
        """
        Adds a new page at the end of the document with the default A4 page size.

        This method has multiple overloads. Arguments are resolved at runtime.

        Raises:
            PdfPageCollectionError: If the operation fails
            TypeError: If no matching overload is found
        """
        self._ensure_not_closed()

        _args = (width, height, page_size)
        _overload_map = {
            (): 'BridgePdfPageCollectionAdd',
            ('float', 'float'): 'BridgePdfPageCollectionAddSingleSingle',
            ('PdfPageSizes',): 'BridgePdfPageCollectionAddPdfPageSizes',
        }

        _bridge_func_name = sdk_helpers.resolve_overload(_overload_map, *_args)
        if _bridge_func_name is None:
            raise TypeError(sdk_helpers.format_overload_error('add', _overload_map, *_args))

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
        return import_module('.pdfpage', package=__package__).PdfPage._from_handle(result)

    def insert(self, index: int, width: Optional[float] = None, height: Optional[float] = None, page_size: Optional[Any] = None) -> 'PdfPage':
        """
        Inserts a new page at the specified position with the default A4 page size.

        This method has multiple overloads. Arguments are resolved at runtime.

        Raises:
            PdfPageCollectionError: If the operation fails
            TypeError: If no matching overload is found
        """
        self._ensure_not_closed()

        _args = (index, width, height, page_size)
        _overload_map = {
            ('int',): 'BridgePdfPageCollectionInsertInt32',
            ('int', 'float', 'float'): 'BridgePdfPageCollectionInsertInt32SingleSingle',
            ('int', 'PdfPageSizes'): 'BridgePdfPageCollectionInsertInt32PdfPageSizes',
        }

        _bridge_func_name = sdk_helpers.resolve_overload(_overload_map, *_args)
        if _bridge_func_name is None:
            raise TypeError(sdk_helpers.format_overload_error('insert', _overload_map, *_args))

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
        return import_module('.pdfpage', package=__package__).PdfPage._from_handle(result)

    def get_enumerator(self) -> Any:
        """
        Returns an enumerator that iterates through the pages collection.

        Returns:
            Any: An enumerator for the pages collection.

        Raises:
            PdfPageCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageCollectionGetEnumerator(self._handle)
        self._check_error()
        return result

    def get_count(self) -> int:
        """
        Gets the number of pages in the collection.

        Returns:
            int: The value of the Count property.

        Raises:
            PdfPageCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageCollectionGetCount(self._handle)
        self._check_error()
        return result

    def get_first(self) -> 'PdfPage':
        """
        Gets the first page of the document, or null if the document has no pages.

        Returns:
            'PdfPage': The value of the First property.

        Raises:
            PdfPageCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageCollectionGetFirst(self._handle)
        self._check_error()
        return import_module('.pdfpage', package=__package__).PdfPage._from_handle(result)

    def get_last(self) -> 'PdfPage':
        """
        Gets the last page of the document, or null if the document has no pages.

        Returns:
            'PdfPage': The value of the Last property.

        Raises:
            PdfPageCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageCollectionGetLast(self._handle)
        self._check_error()
        return import_module('.pdfpage', package=__package__).PdfPage._from_handle(result)

    def get_item(self, index: int) -> 'PdfPage':
        """
        Returns the element at the specified index.

        Args:
            index (int)

        Returns:
            'PdfPage': The element at the specified index.

        Raises:
            PdfPageCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageCollectionGetItemInt32(self._handle, index)
        self._check_error()
        return import_module('.pdfpage', package=__package__).PdfPage._from_handle(result)

    def get_page(self, page_number: int) -> 'PdfPage':
        """
        Returns a page by its 1-based page number.

        Args:
            page_number (int)

        Returns:
            'PdfPage': The with the specified page number.

        Raises:
            PdfPageCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPageCollectionGetPageInt32(self._handle, page_number)
        self._check_error()
        return import_module('.pdfpage', package=__package__).PdfPage._from_handle(result)

    def remove_at(self, index: int) -> None:
        """
        Removes the page at the specified 0-based index.

        Args:
            index (int)

        Returns:
            None: The result of the operation

        Raises:
            PdfPageCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfPageCollectionRemoveAtInt32(self._handle, index)
        self._check_error()

    def swap(self, index1: int, index2: int) -> None:
        """
        Swaps two pages in the document.

        Args:
            index1 (int)
            index2 (int)

        Returns:
            None: The result of the operation

        Raises:
            PdfPageCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfPageCollectionSwapInt32Int32(self._handle, index1, index2)
        self._check_error()

    def move_to(self, source_index: int, destination_index: int) -> None:
        """
        Moves a page from one position to another.

        Args:
            source_index (int)
            destination_index (int)

        Returns:
            None: The result of the operation

        Raises:
            PdfPageCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfPageCollectionMoveToInt32Int32(self._handle, source_index, destination_index)
        self._check_error()

    @property
    def enumerator(self) -> Any:
        """
        Returns an enumerator that iterates through the pages collection.

        Returns:
            Any: An enumerator for the pages collection.
        """
        return self.get_enumerator()

    @property
    def count(self) -> int:
        """
        Gets the number of pages in the collection.

        Returns:
            int: The value of the Count property.
        """
        return self.get_count()

    @property
    def first(self) -> 'PdfPage':
        """
        Gets the first page of the document, or null if the document has no pages.

        Returns:
            'PdfPage': The value of the First property.
        """
        return self.get_first()

    @property
    def last(self) -> 'PdfPage':
        """
        Gets the last page of the document, or null if the document has no pages.

        Returns:
            'PdfPage': The value of the Last property.
        """
        return self.get_last()

    # Collection support for iteration
    def __iter__(self):
        """
        Returns an iterator over the elements in this collection.

        Yields:
            PdfPage: Each element in the collection
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

    def __getitem__(self, index: int) -> 'PdfPage':
        """
        Returns the element at the specified position.

        Args:
            index (int): The index of the element to return (0-based)

        Returns:
            PdfPage: The element at the specified position

        Raises:
            IndexError: If the index is out of range
        """
        if index < 0 or index >= self.get_count():
            raise IndexError(f"Index {index} out of range for collection of size {self.get_count()}")
        return self._get_item(index)

    def _get_item(self, index: int) -> 'PdfPage':
        """Internal method to get item at index."""
        self._ensure_not_closed()
        result = _lib.BridgePdfPageCollectionGetItemInt32(self._handle, index)
        self._check_error()
        return import_module('.pdfpage', package=__package__).PdfPage._from_handle(result)



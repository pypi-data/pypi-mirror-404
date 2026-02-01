"""
PdfFormFieldCollection module.
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


class PdfFormFieldCollectionError(Exception):
    """Exception raised by PdfFormFieldCollection operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfFormFieldCollectionGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfFormFieldCollectionGetLastErrorCode.argtypes = []

_lib.BridgePdfFormFieldCollectionGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionGetLastErrorMessage.argtypes = []

_lib.BridgePdfFormFieldCollectionFreeErrorString.restype = None
_lib.BridgePdfFormFieldCollectionFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldCollectionGetItemInt32.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionGetItemInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfFormFieldCollectionFindByFullNameString.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionFindByFullNameString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfFormFieldCollectionGetEnumerator.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionGetEnumerator.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldCollectionGetCount.restype = ctypes.c_int32
_lib.BridgePdfFormFieldCollectionGetCount.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldCollectionGetItemInt32.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionGetItemInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfFormFieldCollectionRemoveAtInt32.restype = None
_lib.BridgePdfFormFieldCollectionRemoveAtInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfFormFieldCollectionClear.restype = None
_lib.BridgePdfFormFieldCollectionClear.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldCollectionAddTextFieldStringPdfPageSingleSingleSingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionAddTextFieldStringPdfPageSingleSingleSingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]

_lib.BridgePdfFormFieldCollectionAddCheckBoxFieldStringPdfPageSingleSingleSingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionAddCheckBoxFieldStringPdfPageSingleSingleSingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]

_lib.BridgePdfFormFieldCollectionAddRadioButtonFieldStringStringPdfPageSingleSingleSingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionAddRadioButtonFieldStringStringPdfPageSingleSingleSingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]

_lib.BridgePdfFormFieldCollectionAddPushButtonFieldStringPdfPageSingleSingleSingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionAddPushButtonFieldStringPdfPageSingleSingleSingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]

_lib.BridgePdfFormFieldCollectionAddComboBoxFieldStringPdfPageSingleSingleSingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionAddComboBoxFieldStringPdfPageSingleSingleSingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]

_lib.BridgePdfFormFieldCollectionAddListBoxFieldStringPdfPageSingleSingleSingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionAddListBoxFieldStringPdfPageSingleSingleSingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]

_lib.BridgePdfFormFieldCollectionAddSignatureFieldStringPdfPageSingleSingleSingleSingle.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldCollectionAddSignatureFieldStringPdfPageSingleSingleSingleSingle.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]


class PdfFormFieldCollection:
    """
    Represents a collection of form fields in a PDF document. Provides access to the top-level form fields in the document's AcroForm.
    """

    def __init__(self):
        """Cannot instantiate PdfFormFieldCollection directly. Use static factory methods instead."""
        raise TypeError("PdfFormFieldCollection cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfFormFieldCollectionGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfFormFieldCollectionGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfFormFieldCollectionFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfFormFieldCollectionError(f"PdfFormFieldCollection: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfFormFieldCollection instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def find_by_full_name(self, full_name: str) -> 'PdfFormField':
        """
        Finds a form field by its full name (dot-separated path).

        Args:
            full_name (str)

        Returns:
            'PdfFormField': The if found, null otherwise.

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionFindByFullNameString(self._handle, full_name.encode('utf-8') if full_name else None)
        self._check_error()
        return self._create_typed_element(result)

    def get_enumerator(self) -> Any:
        """
        Returns an enumerator that iterates through the form fields collection.

        Returns:
            Any: An enumerator for the form fields collection.

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionGetEnumerator(self._handle)
        self._check_error()
        return result

    def get_count(self) -> int:
        """
        Gets the number of top-level form fields in the document.

        Returns:
            int: The value of the Count property.

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionGetCount(self._handle)
        self._check_error()
        return result

    def get_item(self, index: int) -> 'PdfFormField':
        """
        Returns the element at the specified index.

        Args:
            index (int)

        Returns:
            'PdfFormField': The element at the specified index.

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionGetItemInt32(self._handle, index)
        self._check_error()
        return self._create_typed_element(result)

    def remove_at(self, index: int) -> None:
        """
        Removes the form field at the specified index. This also removes any child fields and associated widget annotations.

        Args:
            index (int)

        Returns:
            None: The result of the operation

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldCollectionRemoveAtInt32(self._handle, index)
        self._check_error()

    def clear(self) -> None:
        """
        Removes all form fields from the document.

        Returns:
            None: The result of the operation

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldCollectionClear(self._handle)
        self._check_error()

    def add_text_field(self, name: str, page: 'PdfPage', x: float, y: float, width: float, height: float) -> 'PdfTextField':
        """
        Adds a new text field to the document on the specified page.

        Args:
            name (str)
            page ('PdfPage')
            x (float)
            y (float)
            width (float)
            height (float)

        Returns:
            'PdfTextField': The newly created .

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionAddTextFieldStringPdfPageSingleSingleSingleSingle(self._handle, name.encode('utf-8') if name else None, page._handle if page else None, x, y, width, height)
        self._check_error()
        return import_module('.pdftextfield', package=__package__).PdfTextField._from_handle(result)

    def add_check_box_field(self, name: str, page: 'PdfPage', x: float, y: float, width: float, height: float) -> 'PdfCheckBoxField':
        """
        Adds a new check box field to the document on the specified page.

        Args:
            name (str)
            page ('PdfPage')
            x (float)
            y (float)
            width (float)
            height (float)

        Returns:
            'PdfCheckBoxField': The newly created .

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionAddCheckBoxFieldStringPdfPageSingleSingleSingleSingle(self._handle, name.encode('utf-8') if name else None, page._handle if page else None, x, y, width, height)
        self._check_error()
        return import_module('.pdfcheckboxfield', package=__package__).PdfCheckBoxField._from_handle(result)

    def add_radio_button_field(self, group_name: str, option_name: str, page: 'PdfPage', x: float, y: float, width: float, height: float) -> 'PdfRadioButtonField':
        """
        Adds a new radio button to an existing or new radio button group on the specified page.

        Args:
            group_name (str)
            option_name (str)
            page ('PdfPage')
            x (float)
            y (float)
            width (float)
            height (float)

        Returns:
            'PdfRadioButtonField': The representing the radio button group.

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionAddRadioButtonFieldStringStringPdfPageSingleSingleSingleSingle(self._handle, group_name.encode('utf-8') if group_name else None, option_name.encode('utf-8') if option_name else None, page._handle if page else None, x, y, width, height)
        self._check_error()
        return import_module('.pdfradiobuttonfield', package=__package__).PdfRadioButtonField._from_handle(result)

    def add_push_button_field(self, name: str, page: 'PdfPage', x: float, y: float, width: float, height: float) -> 'PdfPushButtonField':
        """
        Adds a new push button field to the document on the specified page.

        Args:
            name (str)
            page ('PdfPage')
            x (float)
            y (float)
            width (float)
            height (float)

        Returns:
            'PdfPushButtonField': The newly created .

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionAddPushButtonFieldStringPdfPageSingleSingleSingleSingle(self._handle, name.encode('utf-8') if name else None, page._handle if page else None, x, y, width, height)
        self._check_error()
        return import_module('.pdfpushbuttonfield', package=__package__).PdfPushButtonField._from_handle(result)

    def add_combo_box_field(self, name: str, page: 'PdfPage', x: float, y: float, width: float, height: float) -> 'PdfComboBoxField':
        """
        Adds a new combo box (drop-down list) field to the document on the specified page.

        Args:
            name (str)
            page ('PdfPage')
            x (float)
            y (float)
            width (float)
            height (float)

        Returns:
            'PdfComboBoxField': The newly created .

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionAddComboBoxFieldStringPdfPageSingleSingleSingleSingle(self._handle, name.encode('utf-8') if name else None, page._handle if page else None, x, y, width, height)
        self._check_error()
        return import_module('.pdfcomboboxfield', package=__package__).PdfComboBoxField._from_handle(result)

    def add_list_box_field(self, name: str, page: 'PdfPage', x: float, y: float, width: float, height: float) -> 'PdfListBoxField':
        """
        Adds a new list box field to the document on the specified page.

        Args:
            name (str)
            page ('PdfPage')
            x (float)
            y (float)
            width (float)
            height (float)

        Returns:
            'PdfListBoxField': The newly created .

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionAddListBoxFieldStringPdfPageSingleSingleSingleSingle(self._handle, name.encode('utf-8') if name else None, page._handle if page else None, x, y, width, height)
        self._check_error()
        return import_module('.pdflistboxfield', package=__package__).PdfListBoxField._from_handle(result)

    def add_signature_field(self, name: str, page: 'PdfPage', x: float, y: float, width: float, height: float) -> 'PdfSignatureField':
        """
        Adds a new signature field to the document on the specified page.

        Args:
            name (str)
            page ('PdfPage')
            x (float)
            y (float)
            width (float)
            height (float)

        Returns:
            'PdfSignatureField': The newly created .

        Raises:
            PdfFormFieldCollectionError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldCollectionAddSignatureFieldStringPdfPageSingleSingleSingleSingle(self._handle, name.encode('utf-8') if name else None, page._handle if page else None, x, y, width, height)
        self._check_error()
        return import_module('.pdfsignaturefield', package=__package__).PdfSignatureField._from_handle(result)

    @property
    def enumerator(self) -> Any:
        """
        Returns an enumerator that iterates through the form fields collection.

        Returns:
            Any: An enumerator for the form fields collection.
        """
        return self.get_enumerator()

    @property
    def count(self) -> int:
        """
        Gets the number of top-level form fields in the document.

        Returns:
            int: The value of the Count property.
        """
        return self.get_count()

    # Collection support for iteration
    def __iter__(self):
        """
        Returns an iterator over the elements in this collection.

        Yields:
            PdfFormField: Each element in the collection
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

    def __getitem__(self, index: int) -> 'PdfFormField':
        """
        Returns the element at the specified position.

        Args:
            index (int): The index of the element to return (0-based)

        Returns:
            PdfFormField: The element at the specified position

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
        element_module = import_module('.pdfformfield', package=__package__)
        actual_type = element_module.PdfFormField._get_field_type_from_handle(handle)
        if actual_type is None:
            return element_module.PdfFormField._from_handle(handle)

        # Map enum value to specific subtype
        type_map = {
            'Text': ('pdftextfield', 'PdfTextField'),
            'CheckBox': ('pdfcheckboxfield', 'PdfCheckBoxField'),
            'RadioButton': ('pdfradiobuttonfield', 'PdfRadioButtonField'),
            'PushButton': ('pdfpushbuttonfield', 'PdfPushButtonField'),
            'ComboBox': ('pdfcomboboxfield', 'PdfComboBoxField'),
            'ListBox': ('pdflistboxfield', 'PdfListBoxField'),
            'Signature': ('pdfsignaturefield', 'PdfSignatureField'),
        }

        type_name = actual_type.name if hasattr(actual_type, 'name') else str(actual_type)
        if type_name in type_map:
            module_name, class_name = type_map[type_name]
            subtype_module = import_module('.' + module_name, package=__package__)
            return getattr(subtype_module, class_name)._from_handle(handle)

        # Default to base type
        return element_module.PdfFormField._from_handle(handle)

    def _get_item(self, index: int) -> 'PdfFormField':
        """Internal method to get item at index."""
        self._ensure_not_closed()
        result = _lib.BridgePdfFormFieldCollectionGetItemInt32(self._handle, index)
        self._check_error()
        return self._create_typed_element(result)



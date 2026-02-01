"""
PdfFormField module.
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


class PdfFormFieldError(Exception):
    """Exception raised by PdfFormField operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfFormFieldGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfFormFieldGetLastErrorCode.argtypes = []

_lib.BridgePdfFormFieldGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldGetLastErrorMessage.argtypes = []

_lib.BridgePdfFormFieldFreeErrorString.restype = None
_lib.BridgePdfFormFieldFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldGetName.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldGetName.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldGetFullName.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldGetFullName.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldGetFieldType.restype = ctypes.c_int32
_lib.BridgePdfFormFieldGetFieldType.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldGetValue.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldGetValue.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldSetValueString.restype = None
_lib.BridgePdfFormFieldSetValueString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfFormFieldGetDefaultValue.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldGetDefaultValue.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldGetIsReadOnly.restype = ctypes.c_bool
_lib.BridgePdfFormFieldGetIsReadOnly.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldSetIsReadOnlyBoolean.restype = None
_lib.BridgePdfFormFieldSetIsReadOnlyBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgePdfFormFieldGetIsRequired.restype = ctypes.c_bool
_lib.BridgePdfFormFieldGetIsRequired.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldSetIsRequiredBoolean.restype = None
_lib.BridgePdfFormFieldSetIsRequiredBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgePdfFormFieldGetIsTerminal.restype = ctypes.c_bool
_lib.BridgePdfFormFieldGetIsTerminal.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldGetParent.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldGetParent.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldGetChildCount.restype = ctypes.c_int32
_lib.BridgePdfFormFieldGetChildCount.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldGetWidgetCount.restype = ctypes.c_int32
_lib.BridgePdfFormFieldGetWidgetCount.argtypes = [ctypes.c_void_p]

_lib.BridgePdfFormFieldGetChildInt32.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldGetChildInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfFormFieldGetWidgetInt32.restype = ctypes.c_void_p
_lib.BridgePdfFormFieldGetWidgetInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfFormFieldRemoveChildAtInt32.restype = None
_lib.BridgePdfFormFieldRemoveChildAtInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]


class PdfFormField:
    """
    Represents a form field in a PDF document. Form fields can be terminal (with widget annotations) or non-terminal (with child fields). This is the base class for all form field types. Use the specific subclasses (, , , etc.) for type-specific functionality.
    """

    def __init__(self):
        """Cannot instantiate PdfFormField directly. Use static factory methods instead."""
        raise TypeError("PdfFormField cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfFormFieldGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfFormFieldGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfFormFieldFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfFormFieldError(f"PdfFormField: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfFormField instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    @staticmethod
    def _get_field_type_from_handle(handle):
        """
        Queries the FieldType directly from a native handle without creating a wrapper instance.
        This is used by polymorphic collections to determine the correct subtype.
        """
        result = _lib.BridgePdfFormFieldGetFieldType(handle)
        error_code = _lib.BridgePdfFormFieldGetLastErrorCode()
        if error_code != 0:
            return None
        return import_module('.pdfformfieldtype', package=__package__).PdfFormFieldType(result)

    def get_name(self) -> str:
        """
        Gets the partial name of this field (T entry).

        Returns:
            str: The value of the Name property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_full_name(self) -> str:
        """
        Gets the fully qualified name of this field (dot-separated path from root).

        Returns:
            str: The value of the FullName property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetFullName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_field_type(self) -> Any:
        """
        Gets the type of this form field.

        Returns:
            Any: The value of the FieldType property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetFieldType(self._handle)
        self._check_error()
        return result

    def get_value(self) -> str:
        """
        Gets the current value of the field.

        Returns:
            str: The value of the Value property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetValue(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_value(self, value: str) -> None:
        """
        Sets the current value of the field.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetValueString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_default_value(self) -> str:
        """
        Gets the default value of the field.

        Returns:
            str: The value of the DefaultValue property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetDefaultValue(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_is_read_only(self) -> bool:
        """
        Gets whether the field is read-only.

        Returns:
            bool: The value of the IsReadOnly property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetIsReadOnly(self._handle)
        self._check_error()
        return result

    def set_is_read_only(self, value: bool) -> None:
        """
        Sets whether the field is read-only.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetIsReadOnlyBoolean(self._handle, value)
        self._check_error()

    def get_is_required(self) -> bool:
        """
        Gets whether the field is required.

        Returns:
            bool: The value of the IsRequired property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetIsRequired(self._handle)
        self._check_error()
        return result

    def set_is_required(self, value: bool) -> None:
        """
        Sets whether the field is required.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetIsRequiredBoolean(self._handle, value)
        self._check_error()

    def get_is_terminal(self) -> bool:
        """
        Gets whether this is a terminal field (has widget annotations instead of child fields). Terminal fields represent the actual interactive form elements.

        Returns:
            bool: The value of the IsTerminal property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetIsTerminal(self._handle)
        self._check_error()
        return result

    def get_parent(self) -> 'PdfFormField':
        """
        Gets the parent field of this field, or null if this is a top-level field.

        Returns:
            'PdfFormField': The value of the Parent property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetParent(self._handle)
        self._check_error()
        return import_module('.pdfformfield', package=__package__).PdfFormField._from_handle(result)

    def get_child_count(self) -> int:
        """
        Gets the number of child fields.

        Returns:
            int: The value of the ChildCount property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetChildCount(self._handle)
        self._check_error()
        return result

    def get_widget_count(self) -> int:
        """
        Gets the number of widget annotations.

        Returns:
            int: The value of the WidgetCount property.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetWidgetCount(self._handle)
        self._check_error()
        return result

    def get_child(self, index: int) -> 'PdfFormField':
        """
        Gets a child field by index.

        Args:
            index (int)

        Returns:
            'PdfFormField': The child at the specified index.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetChildInt32(self._handle, index)
        self._check_error()
        return import_module('.pdfformfield', package=__package__).PdfFormField._from_handle(result)

    def get_widget(self, index: int) -> 'PdfWidgetAnnotation':
        """
        Gets a widget annotation by index.

        Args:
            index (int)

        Returns:
            'PdfWidgetAnnotation': The at the specified index.

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetWidgetInt32(self._handle, index)
        self._check_error()
        return import_module('.pdfwidgetannotation', package=__package__).PdfWidgetAnnotation._from_handle(result)

    def remove_child_at(self, index: int) -> None:
        """
        Removes a child field at the specified index. Also removes any grandchild fields and associated widget annotations.

        Args:
            index (int)

        Returns:
            None: The result of the operation

        Raises:
            PdfFormFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldRemoveChildAtInt32(self._handle, index)
        self._check_error()

    @property
    def name(self) -> str:
        """
        Gets the partial name of this field (T entry).

        Returns:
            str: The value of the Name property.
        """
        return self.get_name()

    @property
    def full_name(self) -> str:
        """
        Gets the fully qualified name of this field (dot-separated path from root).

        Returns:
            str: The value of the FullName property.
        """
        return self.get_full_name()

    @property
    def field_type(self) -> Any:
        """
        Gets the type of this form field.

        Returns:
            Any: The value of the FieldType property.
        """
        return self.get_field_type()

    @property
    def value(self) -> str:
        """
        Gets the current value of the field.

        Returns:
            str: The value of the Value property.
        """
        return self.get_value()

    @value.setter
    def value(self, value: str) -> None:
        """
        Sets the value.

        Args:
            value (str): The value to set.
        """
        self.set_value(value)

    @property
    def default_value(self) -> str:
        """
        Gets the default value of the field.

        Returns:
            str: The value of the DefaultValue property.
        """
        return self.get_default_value()

    @property
    def is_read_only(self) -> bool:
        """
        Gets whether the field is read-only.

        Returns:
            bool: The value of the IsReadOnly property.
        """
        return self.get_is_read_only()

    @is_read_only.setter
    def is_read_only(self, value: bool) -> None:
        """
        Sets the is read only.

        Args:
            value (bool): The value to set.
        """
        self.set_is_read_only(value)

    @property
    def is_required(self) -> bool:
        """
        Gets whether the field is required.

        Returns:
            bool: The value of the IsRequired property.
        """
        return self.get_is_required()

    @is_required.setter
    def is_required(self, value: bool) -> None:
        """
        Sets the is required.

        Args:
            value (bool): The value to set.
        """
        self.set_is_required(value)

    @property
    def is_terminal(self) -> bool:
        """
        Gets whether this is a terminal field (has widget annotations instead of child fields). Terminal fields represent the actual interactive form elements.

        Returns:
            bool: The value of the IsTerminal property.
        """
        return self.get_is_terminal()

    @property
    def parent(self) -> 'PdfFormField':
        """
        Gets the parent field of this field, or null if this is a top-level field.

        Returns:
            'PdfFormField': The value of the Parent property.
        """
        return self.get_parent()

    @property
    def child_count(self) -> int:
        """
        Gets the number of child fields.

        Returns:
            int: The value of the ChildCount property.
        """
        return self.get_child_count()

    @property
    def widget_count(self) -> int:
        """
        Gets the number of widget annotations.

        Returns:
            int: The value of the WidgetCount property.
        """
        return self.get_widget_count()



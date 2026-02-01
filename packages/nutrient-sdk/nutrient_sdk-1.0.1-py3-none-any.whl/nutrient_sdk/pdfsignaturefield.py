"""
PdfSignatureField module.
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


class PdfSignatureFieldError(Exception):
    """Exception raised by PdfSignatureField operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfSignatureFieldGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfSignatureFieldGetLastErrorCode.argtypes = []

_lib.BridgePdfSignatureFieldGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfSignatureFieldGetLastErrorMessage.argtypes = []

_lib.BridgePdfSignatureFieldFreeErrorString.restype = None
_lib.BridgePdfSignatureFieldFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSignatureFieldGetIsSigned.restype = ctypes.c_bool
_lib.BridgePdfSignatureFieldGetIsSigned.argtypes = [ctypes.c_void_p]

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


class PdfSignatureField:
    """
    Represents a signature form field in a PDF document. Signature fields are used for electronic signatures.
    """

    def __init__(self):
        """Cannot instantiate PdfSignatureField directly. Use static factory methods instead."""
        raise TypeError("PdfSignatureField cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfSignatureFieldGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfSignatureFieldGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfSignatureFieldFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfSignatureFieldError(f"PdfSignatureField: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfSignatureField instance has been closed")

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
        result = _lib.BridgePdfSignatureFieldGetFieldType(handle)
        error_code = _lib.BridgePdfSignatureFieldGetLastErrorCode()
        if error_code != 0:
            return None
        return import_module('.pdfformfieldtype', package=__package__).PdfFormFieldType(result)

    def get_is_signed(self) -> bool:
        """
        Gets whether the signature field has been signed.

        Returns:
            bool: The value of the IsSigned property.

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfSignatureFieldGetIsSigned(self._handle)
        self._check_error()
        return result

    def get_name(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_full_name(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetFullName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_field_type(self) -> Any:
        """
        Returns:
            Any: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetFieldType(self._handle)
        self._check_error()
        return result

    def get_value(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetValue(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_value(self, value: str) -> None:
        """
        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetValueString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_default_value(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetDefaultValue(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_is_read_only(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetIsReadOnly(self._handle)
        self._check_error()
        return result

    def set_is_read_only(self, value: bool) -> None:
        """
        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetIsReadOnlyBoolean(self._handle, value)
        self._check_error()

    def get_is_required(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetIsRequired(self._handle)
        self._check_error()
        return result

    def set_is_required(self, value: bool) -> None:
        """
        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetIsRequiredBoolean(self._handle, value)
        self._check_error()

    def get_is_terminal(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetIsTerminal(self._handle)
        self._check_error()
        return result

    def get_parent(self) -> 'PdfFormField':
        """
        Returns:
            'PdfFormField': The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetParent(self._handle)
        self._check_error()
        return import_module('.pdfformfield', package=__package__).PdfFormField._from_handle(result)

    def get_child_count(self) -> int:
        """
        Returns:
            int: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetChildCount(self._handle)
        self._check_error()
        return result

    def get_widget_count(self) -> int:
        """
        Returns:
            int: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetWidgetCount(self._handle)
        self._check_error()
        return result

    def get_child(self, index: int) -> 'PdfFormField':
        """
        Args:
            index (int)

        Returns:
            'PdfFormField': The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetChildInt32(self._handle, index)
        self._check_error()
        return import_module('.pdfformfield', package=__package__).PdfFormField._from_handle(result)

    def get_widget(self, index: int) -> 'PdfWidgetAnnotation':
        """
        Args:
            index (int)

        Returns:
            'PdfWidgetAnnotation': The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfFormFieldGetWidgetInt32(self._handle, index)
        self._check_error()
        return import_module('.pdfwidgetannotation', package=__package__).PdfWidgetAnnotation._from_handle(result)

    def remove_child_at(self, index: int) -> None:
        """
        Args:
            index (int)

        Returns:
            None: The result of the operation

        Raises:
            PdfSignatureFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldRemoveChildAtInt32(self._handle, index)
        self._check_error()

    @property
    def is_signed(self) -> bool:
        """
        Gets whether the signature field has been signed.

        Returns:
            bool: The value of the IsSigned property.
        """
        return self.get_is_signed()

    @property
    def name(self) -> str:
        """
        Gets the name.

        Returns:
            str: The value
        """
        return self.get_name()

    @property
    def full_name(self) -> str:
        """
        Gets the full name.

        Returns:
            str: The value
        """
        return self.get_full_name()

    @property
    def field_type(self) -> Any:
        """
        Gets the field type.

        Returns:
            Any: The value
        """
        return self.get_field_type()

    @property
    def value(self) -> str:
        """
        Gets the value.

        Returns:
            str: The value
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
        Gets the default value.

        Returns:
            str: The value
        """
        return self.get_default_value()

    @property
    def is_read_only(self) -> bool:
        """
        Gets the is read only.

        Returns:
            bool: The value
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
        Gets the is required.

        Returns:
            bool: The value
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
        Gets the is terminal.

        Returns:
            bool: The value
        """
        return self.get_is_terminal()

    @property
    def parent(self) -> 'PdfFormField':
        """
        Gets the parent.

        Returns:
            'PdfFormField': The value
        """
        return self.get_parent()

    @property
    def child_count(self) -> int:
        """
        Gets the child count.

        Returns:
            int: The value
        """
        return self.get_child_count()

    @property
    def widget_count(self) -> int:
        """
        Gets the widget count.

        Returns:
            int: The value
        """
        return self.get_widget_count()



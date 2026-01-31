"""
PdfCheckBoxField module.
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


class PdfCheckBoxFieldError(Exception):
    """Exception raised by PdfCheckBoxField operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfCheckBoxFieldGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfCheckBoxFieldGetLastErrorCode.argtypes = []

_lib.BridgePdfCheckBoxFieldGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfCheckBoxFieldGetLastErrorMessage.argtypes = []

_lib.BridgePdfCheckBoxFieldFreeErrorString.restype = None
_lib.BridgePdfCheckBoxFieldFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfCheckBoxFieldGetOnStateName.restype = ctypes.c_void_p
_lib.BridgePdfCheckBoxFieldGetOnStateName.argtypes = [ctypes.c_void_p]

_lib.BridgePdfCheckBoxFieldGetIsChecked.restype = ctypes.c_bool
_lib.BridgePdfCheckBoxFieldGetIsChecked.argtypes = [ctypes.c_void_p]

_lib.BridgePdfCheckBoxFieldSetIsCheckedBoolean.restype = None
_lib.BridgePdfCheckBoxFieldSetIsCheckedBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgePdfCheckBoxFieldGetBackgroundColor.restype = ctypes.c_void_p
_lib.BridgePdfCheckBoxFieldGetBackgroundColor.argtypes = [ctypes.c_void_p]

_lib.BridgePdfCheckBoxFieldSetBackgroundColorColor.restype = None
_lib.BridgePdfCheckBoxFieldSetBackgroundColorColor.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfCheckBoxFieldGetBorderColor.restype = ctypes.c_void_p
_lib.BridgePdfCheckBoxFieldGetBorderColor.argtypes = [ctypes.c_void_p]

_lib.BridgePdfCheckBoxFieldSetBorderColorColor.restype = None
_lib.BridgePdfCheckBoxFieldSetBorderColorColor.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

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


class PdfCheckBoxField:
    """
    Represents a check box form field in a PDF document. Check boxes toggle between two states: checked and unchecked.
    """

    def __init__(self):
        """Cannot instantiate PdfCheckBoxField directly. Use static factory methods instead."""
        raise TypeError("PdfCheckBoxField cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfCheckBoxFieldGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfCheckBoxFieldGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfCheckBoxFieldFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfCheckBoxFieldError(f"PdfCheckBoxField: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfCheckBoxField instance has been closed")

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
        result = _lib.BridgePdfCheckBoxFieldGetFieldType(handle)
        error_code = _lib.BridgePdfCheckBoxFieldGetLastErrorCode()
        if error_code != 0:
            return None
        return import_module('.pdfformfieldtype', package=__package__).PdfFormFieldType(result)

    def get_on_state_name(self) -> str:
        """
        Gets the "on" state name for this check box. This is the value used when the check box is checked (often "Yes" or "On").

        Returns:
            str: The on-state name.

        Raises:
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfCheckBoxFieldGetOnStateName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_is_checked(self) -> bool:
        """
        Gets whether the check box is currently checked.

        Returns:
            bool: The value of the IsChecked property.

        Raises:
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfCheckBoxFieldGetIsChecked(self._handle)
        self._check_error()
        return result

    def set_is_checked(self, value: bool) -> None:
        """
        Sets whether the check box is currently checked.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfCheckBoxFieldSetIsCheckedBoolean(self._handle, value)
        self._check_error()

    def get_background_color(self) -> 'Color':
        """
        Gets the background color of the check box.

        Returns:
            'Color': The value of the BackgroundColor property.

        Raises:
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfCheckBoxFieldGetBackgroundColor(self._handle)
        self._check_error()
        return import_module('.color', package=__package__).Color._from_handle(result)

    def set_background_color(self, value: 'Color') -> None:
        """
        Sets the background color of the check box.

        Args:
            value ('Color')

        Returns:
            None: The result of the operation

        Raises:
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfCheckBoxFieldSetBackgroundColorColor(self._handle, value._handle if value else None)
        self._check_error()

    def get_border_color(self) -> 'Color':
        """
        Gets the border color of the check box.

        Returns:
            'Color': The value of the BorderColor property.

        Raises:
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfCheckBoxFieldGetBorderColor(self._handle)
        self._check_error()
        return import_module('.color', package=__package__).Color._from_handle(result)

    def set_border_color(self, value: 'Color') -> None:
        """
        Sets the border color of the check box.

        Args:
            value ('Color')

        Returns:
            None: The result of the operation

        Raises:
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfCheckBoxFieldSetBorderColorColor(self._handle, value._handle if value else None)
        self._check_error()

    def get_name(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetValueString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_default_value(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetIsReadOnlyBoolean(self._handle, value)
        self._check_error()

    def get_is_required(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetIsRequiredBoolean(self._handle, value)
        self._check_error()

    def get_is_terminal(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
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
            PdfCheckBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldRemoveChildAtInt32(self._handle, index)
        self._check_error()

    @property
    def on_state_name(self) -> str:
        """
        Gets the "on" state name for this check box. This is the value used when the check box is checked (often "Yes" or "On").

        Returns:
            str: The on-state name.
        """
        return self.get_on_state_name()

    @property
    def is_checked(self) -> bool:
        """
        Gets whether the check box is currently checked.

        Returns:
            bool: The value of the IsChecked property.
        """
        return self.get_is_checked()

    @is_checked.setter
    def is_checked(self, value: bool) -> None:
        """
        Sets the is checked.

        Args:
            value (bool): The value to set.
        """
        self.set_is_checked(value)

    @property
    def background_color(self) -> 'Color':
        """
        Gets the background color of the check box.

        Returns:
            'Color': The value of the BackgroundColor property.
        """
        return self.get_background_color()

    @background_color.setter
    def background_color(self, value: 'Color') -> None:
        """
        Sets the background color.

        Args:
            value ('Color'): The value to set.
        """
        self.set_background_color(value)

    @property
    def border_color(self) -> 'Color':
        """
        Gets the border color of the check box.

        Returns:
            'Color': The value of the BorderColor property.
        """
        return self.get_border_color()

    @border_color.setter
    def border_color(self, value: 'Color') -> None:
        """
        Sets the border color.

        Args:
            value ('Color'): The value to set.
        """
        self.set_border_color(value)

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



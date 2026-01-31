"""
PdfListBoxField module.
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


class PdfListBoxFieldError(Exception):
    """Exception raised by PdfListBoxField operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfListBoxFieldGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfListBoxFieldGetLastErrorCode.argtypes = []

_lib.BridgePdfListBoxFieldGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfListBoxFieldGetLastErrorMessage.argtypes = []

_lib.BridgePdfListBoxFieldFreeErrorString.restype = None
_lib.BridgePdfListBoxFieldFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfListBoxFieldGetSelectedValue.restype = ctypes.c_void_p
_lib.BridgePdfListBoxFieldGetSelectedValue.argtypes = [ctypes.c_void_p]

_lib.BridgePdfListBoxFieldSetSelectedValueString.restype = None
_lib.BridgePdfListBoxFieldSetSelectedValueString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfListBoxFieldGetHasSelection.restype = ctypes.c_bool
_lib.BridgePdfListBoxFieldGetHasSelection.argtypes = [ctypes.c_void_p]

_lib.BridgePdfListBoxFieldGetItemCount.restype = ctypes.c_int32
_lib.BridgePdfListBoxFieldGetItemCount.argtypes = [ctypes.c_void_p]

_lib.BridgePdfListBoxFieldAddItemString.restype = None
_lib.BridgePdfListBoxFieldAddItemString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfListBoxFieldAddItemStringString.restype = None
_lib.BridgePdfListBoxFieldAddItemStringString.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfListBoxFieldRemoveItemAtInt32.restype = None
_lib.BridgePdfListBoxFieldRemoveItemAtInt32.argtypes = [ctypes.c_void_p, ctypes.c_int32]

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


class PdfListBoxField:
    """
    Represents a list box form field in a PDF document. List boxes display a scrollable list of options for selection.
    """

    def __init__(self):
        """Cannot instantiate PdfListBoxField directly. Use static factory methods instead."""
        raise TypeError("PdfListBoxField cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfListBoxFieldGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfListBoxFieldGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfListBoxFieldFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfListBoxFieldError(f"PdfListBoxField: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfListBoxField instance has been closed")

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
        result = _lib.BridgePdfListBoxFieldGetFieldType(handle)
        error_code = _lib.BridgePdfListBoxFieldGetLastErrorCode()
        if error_code != 0:
            return None
        return import_module('.pdfformfieldtype', package=__package__).PdfFormFieldType(result)

    def get_selected_value(self) -> str:
        """
        Gets the currently selected value. For multi-select list boxes, this returns the first selected value.

        Returns:
            str: The value of the SelectedValue property.

        Raises:
            PdfListBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfListBoxFieldGetSelectedValue(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_selected_value(self, value: str) -> None:
        """
        Sets the currently selected value. For multi-select list boxes, this returns the first selected value.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfListBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfListBoxFieldSetSelectedValueString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_has_selection(self) -> bool:
        """
        Gets whether the list box has a value selected.

        Returns:
            bool: The value of the HasSelection property.

        Raises:
            PdfListBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfListBoxFieldGetHasSelection(self._handle)
        self._check_error()
        return result

    def get_item_count(self) -> int:
        """
        Gets the number of items in the list box.

        Returns:
            int: The value of the ItemCount property.

        Raises:
            PdfListBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfListBoxFieldGetItemCount(self._handle)
        self._check_error()
        return result

    def add_item(self, text: str, value: Optional[str] = None) -> None:
        """
        Adds an item to the list box.

        This method has multiple overloads. Arguments are resolved at runtime.

        Raises:
            PdfListBoxFieldError: If the operation fails
            TypeError: If no matching overload is found
        """
        self._ensure_not_closed()

        _args = (text, value)
        _overload_map = {
            ('str',): 'BridgePdfListBoxFieldAddItemString',
            ('str', 'str'): 'BridgePdfListBoxFieldAddItemStringString',
        }

        _bridge_func_name = sdk_helpers.resolve_overload(_overload_map, *_args)
        if _bridge_func_name is None:
            raise TypeError(sdk_helpers.format_overload_error('add_item', _overload_map, *_args))

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

    def remove_item_at(self, index: int) -> None:
        """
        Removes an item from the list box at the specified index.

        Args:
            index (int)

        Returns:
            None: The result of the operation

        Raises:
            PdfListBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfListBoxFieldRemoveItemAtInt32(self._handle, index)
        self._check_error()

    def get_name(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetValueString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_default_value(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetIsReadOnlyBoolean(self._handle, value)
        self._check_error()

    def get_is_required(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetIsRequiredBoolean(self._handle, value)
        self._check_error()

    def get_is_terminal(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
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
            PdfListBoxFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldRemoveChildAtInt32(self._handle, index)
        self._check_error()

    @property
    def selected_value(self) -> str:
        """
        Gets the currently selected value. For multi-select list boxes, this returns the first selected value.

        Returns:
            str: The value of the SelectedValue property.
        """
        return self.get_selected_value()

    @selected_value.setter
    def selected_value(self, value: str) -> None:
        """
        Sets the selected value.

        Args:
            value (str): The value to set.
        """
        self.set_selected_value(value)

    @property
    def has_selection(self) -> bool:
        """
        Gets whether the list box has a value selected.

        Returns:
            bool: The value of the HasSelection property.
        """
        return self.get_has_selection()

    @property
    def item_count(self) -> int:
        """
        Gets the number of items in the list box.

        Returns:
            int: The value of the ItemCount property.
        """
        return self.get_item_count()

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



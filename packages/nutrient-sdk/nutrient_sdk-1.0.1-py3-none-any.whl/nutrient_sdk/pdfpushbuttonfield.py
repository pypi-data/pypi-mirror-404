"""
PdfPushButtonField module.
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


class PdfPushButtonFieldError(Exception):
    """Exception raised by PdfPushButtonField operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfPushButtonFieldGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfPushButtonFieldGetLastErrorCode.argtypes = []

_lib.BridgePdfPushButtonFieldGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfPushButtonFieldGetLastErrorMessage.argtypes = []

_lib.BridgePdfPushButtonFieldFreeErrorString.restype = None
_lib.BridgePdfPushButtonFieldFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldGetCaption.restype = ctypes.c_void_p
_lib.BridgePdfPushButtonFieldGetCaption.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldSetCaptionString.restype = None
_lib.BridgePdfPushButtonFieldSetCaptionString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldGetFontName.restype = ctypes.c_void_p
_lib.BridgePdfPushButtonFieldGetFontName.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldSetFontNameString.restype = None
_lib.BridgePdfPushButtonFieldSetFontNameString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldGetFontSize.restype = ctypes.c_float
_lib.BridgePdfPushButtonFieldGetFontSize.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldSetFontSizeSingle.restype = None
_lib.BridgePdfPushButtonFieldSetFontSizeSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgePdfPushButtonFieldGetFontColor.restype = ctypes.c_void_p
_lib.BridgePdfPushButtonFieldGetFontColor.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldSetFontColorColor.restype = None
_lib.BridgePdfPushButtonFieldSetFontColorColor.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldGetBackgroundColor.restype = ctypes.c_void_p
_lib.BridgePdfPushButtonFieldGetBackgroundColor.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldSetBackgroundColorColor.restype = None
_lib.BridgePdfPushButtonFieldSetBackgroundColorColor.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldGetBorderColor.restype = ctypes.c_void_p
_lib.BridgePdfPushButtonFieldGetBorderColor.argtypes = [ctypes.c_void_p]

_lib.BridgePdfPushButtonFieldSetBorderColorColor.restype = None
_lib.BridgePdfPushButtonFieldSetBorderColorColor.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

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


class PdfPushButtonField:
    """
    Represents a push button form field in a PDF document. Push buttons respond immediately to user input without retaining a permanent value. They are typically used to trigger actions like submit, reset, or JavaScript execution.
    """

    def __init__(self):
        """Cannot instantiate PdfPushButtonField directly. Use static factory methods instead."""
        raise TypeError("PdfPushButtonField cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfPushButtonFieldGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfPushButtonFieldGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfPushButtonFieldFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfPushButtonFieldError(f"PdfPushButtonField: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfPushButtonField instance has been closed")

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
        result = _lib.BridgePdfPushButtonFieldGetFieldType(handle)
        error_code = _lib.BridgePdfPushButtonFieldGetLastErrorCode()
        if error_code != 0:
            return None
        return import_module('.pdfformfieldtype', package=__package__).PdfFormFieldType(result)

    def get_caption(self) -> str:
        """
        Gets the caption text displayed on the button.

        Returns:
            str: The value of the Caption property.

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPushButtonFieldGetCaption(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_caption(self, value: str) -> None:
        """
        Sets the caption text displayed on the button.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfPushButtonFieldSetCaptionString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_font_name(self) -> str:
        """
        Gets the font name for the button caption text.

        Returns:
            str: The value of the FontName property.

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPushButtonFieldGetFontName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_font_name(self, value: str) -> None:
        """
        Sets the font name for the button caption text.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfPushButtonFieldSetFontNameString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_font_size(self) -> float:
        """
        Gets the font size for the button caption text.

        Returns:
            float: The value of the FontSize property.

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPushButtonFieldGetFontSize(self._handle)
        self._check_error()
        return result

    def set_font_size(self, value: float) -> None:
        """
        Sets the font size for the button caption text.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfPushButtonFieldSetFontSizeSingle(self._handle, value)
        self._check_error()

    def get_font_color(self) -> 'Color':
        """
        Gets the font color for the button caption text.

        Returns:
            'Color': The value of the FontColor property.

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPushButtonFieldGetFontColor(self._handle)
        self._check_error()
        return import_module('.color', package=__package__).Color._from_handle(result)

    def set_font_color(self, value: 'Color') -> None:
        """
        Sets the font color for the button caption text.

        Args:
            value ('Color')

        Returns:
            None: The result of the operation

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfPushButtonFieldSetFontColorColor(self._handle, value._handle if value else None)
        self._check_error()

    def get_background_color(self) -> 'Color':
        """
        Gets the background color of the button.

        Returns:
            'Color': The value of the BackgroundColor property.

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPushButtonFieldGetBackgroundColor(self._handle)
        self._check_error()
        return import_module('.color', package=__package__).Color._from_handle(result)

    def set_background_color(self, value: 'Color') -> None:
        """
        Sets the background color of the button.

        Args:
            value ('Color')

        Returns:
            None: The result of the operation

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfPushButtonFieldSetBackgroundColorColor(self._handle, value._handle if value else None)
        self._check_error()

    def get_border_color(self) -> 'Color':
        """
        Gets the border color of the button.

        Returns:
            'Color': The value of the BorderColor property.

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfPushButtonFieldGetBorderColor(self._handle)
        self._check_error()
        return import_module('.color', package=__package__).Color._from_handle(result)

    def set_border_color(self, value: 'Color') -> None:
        """
        Sets the border color of the button.

        Args:
            value ('Color')

        Returns:
            None: The result of the operation

        Raises:
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfPushButtonFieldSetBorderColorColor(self._handle, value._handle if value else None)
        self._check_error()

    def get_name(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetValueString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_default_value(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetIsReadOnlyBoolean(self._handle, value)
        self._check_error()

    def get_is_required(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldSetIsRequiredBoolean(self._handle, value)
        self._check_error()

    def get_is_terminal(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
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
            PdfPushButtonFieldError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfFormFieldRemoveChildAtInt32(self._handle, index)
        self._check_error()

    @property
    def caption(self) -> str:
        """
        Gets the caption text displayed on the button.

        Returns:
            str: The value of the Caption property.
        """
        return self.get_caption()

    @caption.setter
    def caption(self, value: str) -> None:
        """
        Sets the caption.

        Args:
            value (str): The value to set.
        """
        self.set_caption(value)

    @property
    def font_name(self) -> str:
        """
        Gets the font name for the button caption text.

        Returns:
            str: The value of the FontName property.
        """
        return self.get_font_name()

    @font_name.setter
    def font_name(self, value: str) -> None:
        """
        Sets the font name.

        Args:
            value (str): The value to set.
        """
        self.set_font_name(value)

    @property
    def font_size(self) -> float:
        """
        Gets the font size for the button caption text.

        Returns:
            float: The value of the FontSize property.
        """
        return self.get_font_size()

    @font_size.setter
    def font_size(self, value: float) -> None:
        """
        Sets the font size.

        Args:
            value (float): The value to set.
        """
        self.set_font_size(value)

    @property
    def font_color(self) -> 'Color':
        """
        Gets the font color for the button caption text.

        Returns:
            'Color': The value of the FontColor property.
        """
        return self.get_font_color()

    @font_color.setter
    def font_color(self, value: 'Color') -> None:
        """
        Sets the font color.

        Args:
            value ('Color'): The value to set.
        """
        self.set_font_color(value)

    @property
    def background_color(self) -> 'Color':
        """
        Gets the background color of the button.

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
        Gets the border color of the button.

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



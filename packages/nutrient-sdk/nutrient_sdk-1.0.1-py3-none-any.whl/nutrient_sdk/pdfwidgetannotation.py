"""
PdfWidgetAnnotation module.
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


class PdfWidgetAnnotationError(Exception):
    """Exception raised by PdfWidgetAnnotation operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfWidgetAnnotationGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfWidgetAnnotationGetLastErrorCode.argtypes = []

_lib.BridgePdfWidgetAnnotationGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfWidgetAnnotationGetLastErrorMessage.argtypes = []

_lib.BridgePdfWidgetAnnotationFreeErrorString.restype = None
_lib.BridgePdfWidgetAnnotationFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfWidgetAnnotationGetFieldName.restype = ctypes.c_void_p
_lib.BridgePdfWidgetAnnotationGetFieldName.argtypes = [ctypes.c_void_p]

_lib.BridgePdfWidgetAnnotationGetAlternateFieldName.restype = ctypes.c_void_p
_lib.BridgePdfWidgetAnnotationGetAlternateFieldName.argtypes = [ctypes.c_void_p]

_lib.BridgePdfWidgetAnnotationGetFieldType.restype = ctypes.c_void_p
_lib.BridgePdfWidgetAnnotationGetFieldType.argtypes = [ctypes.c_void_p]

_lib.BridgePdfWidgetAnnotationGetIsTextField.restype = ctypes.c_bool
_lib.BridgePdfWidgetAnnotationGetIsTextField.argtypes = [ctypes.c_void_p]

_lib.BridgePdfWidgetAnnotationGetIsButton.restype = ctypes.c_bool
_lib.BridgePdfWidgetAnnotationGetIsButton.argtypes = [ctypes.c_void_p]

_lib.BridgePdfWidgetAnnotationGetIsChoiceField.restype = ctypes.c_bool
_lib.BridgePdfWidgetAnnotationGetIsChoiceField.argtypes = [ctypes.c_void_p]

_lib.BridgePdfWidgetAnnotationGetIsSignatureField.restype = ctypes.c_bool
_lib.BridgePdfWidgetAnnotationGetIsSignatureField.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationGetIndex.restype = ctypes.c_int32
_lib.BridgePdfAnnotationGetIndex.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationGetSubType.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationGetSubType.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationGetRect.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationGetRect.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationSetRectNullableRectF.restype = None
_lib.BridgePdfAnnotationSetRectNullableRectF.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_bool]

_lib.BridgePdfAnnotationGetColor.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationGetColor.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationSetColorColor.restype = None
_lib.BridgePdfAnnotationSetColorColor.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationGetBorderWidth.restype = ctypes.c_float
_lib.BridgePdfAnnotationGetBorderWidth.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationSetBorderWidthSingle.restype = None
_lib.BridgePdfAnnotationSetBorderWidthSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgePdfAnnotationGetBorderStyle.restype = ctypes.c_int32
_lib.BridgePdfAnnotationGetBorderStyle.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationSetBorderStylePdfBorderStyle.restype = None
_lib.BridgePdfAnnotationSetBorderStylePdfBorderStyle.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgePdfAnnotationGetTitle.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationGetTitle.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationSetTitleString.restype = None
_lib.BridgePdfAnnotationSetTitleString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationGetContents.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationGetContents.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationSetContentsString.restype = None
_lib.BridgePdfAnnotationSetContentsString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfAnnotationGetModificationDate.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationGetModificationDate.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationGetName.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationGetName.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationGetIsHidden.restype = ctypes.c_bool
_lib.BridgePdfAnnotationGetIsHidden.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationSetIsHiddenBoolean.restype = None
_lib.BridgePdfAnnotationSetIsHiddenBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgePdfAnnotationGetIsPrintable.restype = ctypes.c_bool
_lib.BridgePdfAnnotationGetIsPrintable.argtypes = [ctypes.c_void_p]

_lib.BridgePdfAnnotationSetIsPrintableBoolean.restype = None
_lib.BridgePdfAnnotationSetIsPrintableBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]


class PdfWidgetAnnotation:
    """
    Represents a widget annotation (form field).
    """

    def __init__(self):
        """Cannot instantiate PdfWidgetAnnotation directly. Use static factory methods instead."""
        raise TypeError("PdfWidgetAnnotation cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfWidgetAnnotationGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfWidgetAnnotationGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfWidgetAnnotationFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfWidgetAnnotationError(f"PdfWidgetAnnotation: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfWidgetAnnotation instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    @staticmethod
    def _get_sub_type_from_handle(handle):
        """
        Queries the SubType directly from a native handle without creating a wrapper instance.
        This is used by polymorphic collections to determine the correct subtype.
        """
        result = _lib.BridgePdfWidgetAnnotationGetSubType(handle)
        error_code = _lib.BridgePdfWidgetAnnotationGetLastErrorCode()
        if error_code != 0:
            return None
        return sdk_loader.convert_string_handle(result)

    def get_field_name(self) -> str:
        """
        Gets the field name (partial name).

        Returns:
            str: The value of the FieldName property.

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfWidgetAnnotationGetFieldName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_alternate_field_name(self) -> str:
        """
        Gets the alternate field name for display.

        Returns:
            str: The value of the AlternateFieldName property.

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfWidgetAnnotationGetAlternateFieldName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_field_type(self) -> str:
        """
        Gets the field type (Tx, Btn, Ch, Sig).

        Returns:
            str: The value of the FieldType property.

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfWidgetAnnotationGetFieldType(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_is_text_field(self) -> bool:
        """
        Gets whether this is a text field.

        Returns:
            bool: The value of the IsTextField property.

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfWidgetAnnotationGetIsTextField(self._handle)
        self._check_error()
        return result

    def get_is_button(self) -> bool:
        """
        Gets whether this is a button (checkbox, radio button, or push button).

        Returns:
            bool: The value of the IsButton property.

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfWidgetAnnotationGetIsButton(self._handle)
        self._check_error()
        return result

    def get_is_choice_field(self) -> bool:
        """
        Gets whether this is a choice field (combo box or list box).

        Returns:
            bool: The value of the IsChoiceField property.

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfWidgetAnnotationGetIsChoiceField(self._handle)
        self._check_error()
        return result

    def get_is_signature_field(self) -> bool:
        """
        Gets whether this is a signature field.

        Returns:
            bool: The value of the IsSignatureField property.

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfWidgetAnnotationGetIsSignatureField(self._handle)
        self._check_error()
        return result

    def get_index(self) -> int:
        """
        Returns:
            int: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetIndex(self._handle)
        self._check_error()
        return result

    def get_sub_type(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetSubType(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_rect(self) -> Optional[Any]:
        """
        Returns:
            Optional[Any]: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetRect(self._handle)
        self._check_error()
        return result

    def set_rect(self, value: Optional[Any]) -> None:
        """
        Args:
            value (Optional[Any])

        Returns:
            None: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetRectNullableRectF(self._handle, value.left if value is not None else 0.0, value.top if value is not None else 0.0, value.right if value is not None else 0.0, value.bottom if value is not None else 0.0, value is not None)
        self._check_error()

    def get_color(self) -> 'Color':
        """
        Returns:
            'Color': The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetColor(self._handle)
        self._check_error()
        return import_module('.color', package=__package__).Color._from_handle(result)

    def set_color(self, value: 'Color') -> None:
        """
        Args:
            value ('Color')

        Returns:
            None: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetColorColor(self._handle, value._handle if value else None)
        self._check_error()

    def get_border_width(self) -> float:
        """
        Returns:
            float: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetBorderWidth(self._handle)
        self._check_error()
        return result

    def set_border_width(self, value: float) -> None:
        """
        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetBorderWidthSingle(self._handle, value)
        self._check_error()

    def get_border_style(self) -> Any:
        """
        Returns:
            Any: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetBorderStyle(self._handle)
        self._check_error()
        return result

    def set_border_style(self, value: Any) -> None:
        """
        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetBorderStylePdfBorderStyle(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_title(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetTitle(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_title(self, value: str) -> None:
        """
        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetTitleString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_contents(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetContents(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_contents(self, value: str) -> None:
        """
        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetContentsString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_modification_date(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetModificationDate(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_name(self) -> str:
        """
        Returns:
            str: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_is_hidden(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetIsHidden(self._handle)
        self._check_error()
        return result

    def set_is_hidden(self, value: bool) -> None:
        """
        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetIsHiddenBoolean(self._handle, value)
        self._check_error()

    def get_is_printable(self) -> bool:
        """
        Returns:
            bool: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetIsPrintable(self._handle)
        self._check_error()
        return result

    def set_is_printable(self, value: bool) -> None:
        """
        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfWidgetAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetIsPrintableBoolean(self._handle, value)
        self._check_error()

    @property
    def field_name(self) -> str:
        """
        Gets the field name (partial name).

        Returns:
            str: The value of the FieldName property.
        """
        return self.get_field_name()

    @property
    def alternate_field_name(self) -> str:
        """
        Gets the alternate field name for display.

        Returns:
            str: The value of the AlternateFieldName property.
        """
        return self.get_alternate_field_name()

    @property
    def field_type(self) -> str:
        """
        Gets the field type (Tx, Btn, Ch, Sig).

        Returns:
            str: The value of the FieldType property.
        """
        return self.get_field_type()

    @property
    def is_text_field(self) -> bool:
        """
        Gets whether this is a text field.

        Returns:
            bool: The value of the IsTextField property.
        """
        return self.get_is_text_field()

    @property
    def is_button(self) -> bool:
        """
        Gets whether this is a button (checkbox, radio button, or push button).

        Returns:
            bool: The value of the IsButton property.
        """
        return self.get_is_button()

    @property
    def is_choice_field(self) -> bool:
        """
        Gets whether this is a choice field (combo box or list box).

        Returns:
            bool: The value of the IsChoiceField property.
        """
        return self.get_is_choice_field()

    @property
    def is_signature_field(self) -> bool:
        """
        Gets whether this is a signature field.

        Returns:
            bool: The value of the IsSignatureField property.
        """
        return self.get_is_signature_field()

    @property
    def index(self) -> int:
        """
        Gets the index.

        Returns:
            int: The value
        """
        return self.get_index()

    @property
    def sub_type(self) -> str:
        """
        Gets the sub type.

        Returns:
            str: The value
        """
        return self.get_sub_type()

    @property
    def rect(self) -> Optional[Any]:
        """
        Gets the rect.

        Returns:
            Optional[Any]: The value
        """
        return self.get_rect()

    @rect.setter
    def rect(self, value: Optional[Any]) -> None:
        """
        Sets the rect.

        Args:
            value (Optional[Any]): The value to set.
        """
        self.set_rect(value)

    @property
    def color(self) -> 'Color':
        """
        Gets the color.

        Returns:
            'Color': The value
        """
        return self.get_color()

    @color.setter
    def color(self, value: 'Color') -> None:
        """
        Sets the color.

        Args:
            value ('Color'): The value to set.
        """
        self.set_color(value)

    @property
    def border_width(self) -> float:
        """
        Gets the border width.

        Returns:
            float: The value
        """
        return self.get_border_width()

    @border_width.setter
    def border_width(self, value: float) -> None:
        """
        Sets the border width.

        Args:
            value (float): The value to set.
        """
        self.set_border_width(value)

    @property
    def border_style(self) -> Any:
        """
        Gets the border style.

        Returns:
            Any: The value
        """
        return self.get_border_style()

    @border_style.setter
    def border_style(self, value: Any) -> None:
        """
        Sets the border style.

        Args:
            value (Any): The value to set.
        """
        self.set_border_style(value)

    @property
    def title(self) -> str:
        """
        Gets the title.

        Returns:
            str: The value
        """
        return self.get_title()

    @title.setter
    def title(self, value: str) -> None:
        """
        Sets the title.

        Args:
            value (str): The value to set.
        """
        self.set_title(value)

    @property
    def contents(self) -> str:
        """
        Gets the contents.

        Returns:
            str: The value
        """
        return self.get_contents()

    @contents.setter
    def contents(self, value: str) -> None:
        """
        Sets the contents.

        Args:
            value (str): The value to set.
        """
        self.set_contents(value)

    @property
    def modification_date(self) -> str:
        """
        Gets the modification date.

        Returns:
            str: The value
        """
        return self.get_modification_date()

    @property
    def name(self) -> str:
        """
        Gets the name.

        Returns:
            str: The value
        """
        return self.get_name()

    @property
    def is_hidden(self) -> bool:
        """
        Gets the is hidden.

        Returns:
            bool: The value
        """
        return self.get_is_hidden()

    @is_hidden.setter
    def is_hidden(self, value: bool) -> None:
        """
        Sets the is hidden.

        Args:
            value (bool): The value to set.
        """
        self.set_is_hidden(value)

    @property
    def is_printable(self) -> bool:
        """
        Gets the is printable.

        Returns:
            bool: The value
        """
        return self.get_is_printable()

    @is_printable.setter
    def is_printable(self, value: bool) -> None:
        """
        Sets the is printable.

        Args:
            value (bool): The value to set.
        """
        self.set_is_printable(value)



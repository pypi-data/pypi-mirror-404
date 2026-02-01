"""
PdfAnnotation module.
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


class PdfAnnotationError(Exception):
    """Exception raised by PdfAnnotation operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfAnnotationGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfAnnotationGetLastErrorCode.argtypes = []

_lib.BridgePdfAnnotationGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfAnnotationGetLastErrorMessage.argtypes = []

_lib.BridgePdfAnnotationFreeErrorString.restype = None
_lib.BridgePdfAnnotationFreeErrorString.argtypes = [ctypes.c_void_p]

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


class PdfAnnotation:
    """
    Represents a base annotation in a PDF document.
    """

    def __init__(self):
        """Cannot instantiate PdfAnnotation directly. Use static factory methods instead."""
        raise TypeError("PdfAnnotation cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfAnnotationGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfAnnotationGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfAnnotationFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfAnnotationError(f"PdfAnnotation: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfAnnotation instance has been closed")

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
        result = _lib.BridgePdfAnnotationGetSubType(handle)
        error_code = _lib.BridgePdfAnnotationGetLastErrorCode()
        if error_code != 0:
            return None
        return sdk_loader.convert_string_handle(result)

    def get_index(self) -> int:
        """
        Gets the 0-based index of this annotation in the page's annotation array.

        Returns:
            int: The value of the Index property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetIndex(self._handle)
        self._check_error()
        return result

    def get_sub_type(self) -> str:
        """
        Gets the annotation subtype (e.g., "Text", "Link", "Highlight").

        Returns:
            str: The value of the SubType property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetSubType(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_rect(self) -> Optional[Any]:
        """
        Gets the rectangle that defines the location and size of the annotation on the page.

        Returns:
            Optional[Any]: The value of the Rect property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetRect(self._handle)
        self._check_error()
        return result

    def set_rect(self, value: Optional[Any]) -> None:
        """
        Sets the rectangle that defines the location and size of the annotation on the page.

        Args:
            value (Optional[Any])

        Returns:
            None: The result of the operation

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetRectNullableRectF(self._handle, value.left if value is not None else 0.0, value.top if value is not None else 0.0, value.right if value is not None else 0.0, value.bottom if value is not None else 0.0, value is not None)
        self._check_error()

    def get_color(self) -> 'Color':
        """
        Gets the annotation color.

        Returns:
            'Color': The value of the Color property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetColor(self._handle)
        self._check_error()
        return import_module('.color', package=__package__).Color._from_handle(result)

    def set_color(self, value: 'Color') -> None:
        """
        Sets the annotation color.

        Args:
            value ('Color')

        Returns:
            None: The result of the operation

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetColorColor(self._handle, value._handle if value else None)
        self._check_error()

    def get_border_width(self) -> float:
        """
        Gets the border width of the annotation in points.

        Returns:
            float: The value of the BorderWidth property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetBorderWidth(self._handle)
        self._check_error()
        return result

    def set_border_width(self, value: float) -> None:
        """
        Sets the border width of the annotation in points.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetBorderWidthSingle(self._handle, value)
        self._check_error()

    def get_border_style(self) -> Any:
        """
        Gets the border style of the annotation.

        Returns:
            Any: The value of the BorderStyle property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetBorderStyle(self._handle)
        self._check_error()
        return result

    def set_border_style(self, value: Any) -> None:
        """
        Sets the border style of the annotation.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetBorderStylePdfBorderStyle(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_title(self) -> str:
        """
        Gets the annotation's title/author.

        Returns:
            str: The value of the Title property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetTitle(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_title(self, value: str) -> None:
        """
        Sets the annotation's title/author.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetTitleString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_contents(self) -> str:
        """
        Gets the annotation's text contents.

        Returns:
            str: The value of the Contents property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetContents(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_contents(self, value: str) -> None:
        """
        Sets the annotation's text contents.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetContentsString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_modification_date(self) -> str:
        """
        Gets the annotation's modification date.

        Returns:
            str: The value of the ModificationDate property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetModificationDate(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_name(self) -> str:
        """
        Gets the annotation's unique name/identifier.

        Returns:
            str: The value of the Name property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_is_hidden(self) -> bool:
        """
        Gets whether the annotation is hidden.

        Returns:
            bool: The value of the IsHidden property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetIsHidden(self._handle)
        self._check_error()
        return result

    def set_is_hidden(self, value: bool) -> None:
        """
        Sets whether the annotation is hidden.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetIsHiddenBoolean(self._handle, value)
        self._check_error()

    def get_is_printable(self) -> bool:
        """
        Gets whether the annotation is printable.

        Returns:
            bool: The value of the IsPrintable property.

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfAnnotationGetIsPrintable(self._handle)
        self._check_error()
        return result

    def set_is_printable(self, value: bool) -> None:
        """
        Sets whether the annotation is printable.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            PdfAnnotationError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfAnnotationSetIsPrintableBoolean(self._handle, value)
        self._check_error()

    @property
    def index(self) -> int:
        """
        Gets the 0-based index of this annotation in the page's annotation array.

        Returns:
            int: The value of the Index property.
        """
        return self.get_index()

    @property
    def sub_type(self) -> str:
        """
        Gets the annotation subtype (e.g., "Text", "Link", "Highlight").

        Returns:
            str: The value of the SubType property.
        """
        return self.get_sub_type()

    @property
    def rect(self) -> Optional[Any]:
        """
        Gets the rectangle that defines the location and size of the annotation on the page.

        Returns:
            Optional[Any]: The value of the Rect property.
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
        Gets the annotation color.

        Returns:
            'Color': The value of the Color property.
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
        Gets the border width of the annotation in points.

        Returns:
            float: The value of the BorderWidth property.
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
        Gets the border style of the annotation.

        Returns:
            Any: The value of the BorderStyle property.
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
        Gets the annotation's title/author.

        Returns:
            str: The value of the Title property.
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
        Gets the annotation's text contents.

        Returns:
            str: The value of the Contents property.
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
        Gets the annotation's modification date.

        Returns:
            str: The value of the ModificationDate property.
        """
        return self.get_modification_date()

    @property
    def name(self) -> str:
        """
        Gets the annotation's unique name/identifier.

        Returns:
            str: The value of the Name property.
        """
        return self.get_name()

    @property
    def is_hidden(self) -> bool:
        """
        Gets whether the annotation is hidden.

        Returns:
            bool: The value of the IsHidden property.
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
        Gets whether the annotation is printable.

        Returns:
            bool: The value of the IsPrintable property.
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



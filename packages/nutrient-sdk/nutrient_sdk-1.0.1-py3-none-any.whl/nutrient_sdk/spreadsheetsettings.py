"""
SpreadsheetSettings module.
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


class SpreadsheetSettingsError(Exception):
    """Exception raised by SpreadsheetSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeSpreadsheetSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeSpreadsheetSettingsGetLastErrorCode.argtypes = []

_lib.BridgeSpreadsheetSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeSpreadsheetSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeSpreadsheetSettingsFreeErrorString.restype = None
_lib.BridgeSpreadsheetSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsGetSplitSheetsIntoPages.restype = ctypes.c_bool
_lib.BridgeSpreadsheetSettingsGetSplitSheetsIntoPages.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetSplitSheetsIntoPagesBoolean.restype = None
_lib.BridgeSpreadsheetSettingsSetSplitSheetsIntoPagesBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeSpreadsheetSettingsGetRenderSheetHeadersAndFooters.restype = ctypes.c_bool
_lib.BridgeSpreadsheetSettingsGetRenderSheetHeadersAndFooters.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetRenderSheetHeadersAndFootersBoolean.restype = None
_lib.BridgeSpreadsheetSettingsSetRenderSheetHeadersAndFootersBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeSpreadsheetSettingsGetRenderOnlyPrintArea.restype = ctypes.c_bool
_lib.BridgeSpreadsheetSettingsGetRenderOnlyPrintArea.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetRenderOnlyPrintAreaBoolean.restype = None
_lib.BridgeSpreadsheetSettingsSetRenderOnlyPrintAreaBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeSpreadsheetSettingsGetHalfTransparentHeaderFooter.restype = ctypes.c_bool
_lib.BridgeSpreadsheetSettingsGetHalfTransparentHeaderFooter.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetHalfTransparentHeaderFooterBoolean.restype = None
_lib.BridgeSpreadsheetSettingsSetHalfTransparentHeaderFooterBoolean.argtypes = [ctypes.c_void_p, ctypes.c_bool]

_lib.BridgeSpreadsheetSettingsGetPageHeightOverride.restype = ctypes.c_float
_lib.BridgeSpreadsheetSettingsGetPageHeightOverride.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetPageHeightOverrideSingle.restype = None
_lib.BridgeSpreadsheetSettingsSetPageHeightOverrideSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeSpreadsheetSettingsGetPageWidthOverride.restype = ctypes.c_float
_lib.BridgeSpreadsheetSettingsGetPageWidthOverride.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetPageWidthOverrideSingle.restype = None
_lib.BridgeSpreadsheetSettingsSetPageWidthOverrideSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeSpreadsheetSettingsGetLeftMarginOverride.restype = ctypes.c_float
_lib.BridgeSpreadsheetSettingsGetLeftMarginOverride.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetLeftMarginOverrideSingle.restype = None
_lib.BridgeSpreadsheetSettingsSetLeftMarginOverrideSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeSpreadsheetSettingsGetTopMarginOverride.restype = ctypes.c_float
_lib.BridgeSpreadsheetSettingsGetTopMarginOverride.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetTopMarginOverrideSingle.restype = None
_lib.BridgeSpreadsheetSettingsSetTopMarginOverrideSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeSpreadsheetSettingsGetRightMarginOverride.restype = ctypes.c_float
_lib.BridgeSpreadsheetSettingsGetRightMarginOverride.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetRightMarginOverrideSingle.restype = None
_lib.BridgeSpreadsheetSettingsSetRightMarginOverrideSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeSpreadsheetSettingsGetBottomMarginOverride.restype = ctypes.c_float
_lib.BridgeSpreadsheetSettingsGetBottomMarginOverride.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetBottomMarginOverrideSingle.restype = None
_lib.BridgeSpreadsheetSettingsSetBottomMarginOverrideSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeSpreadsheetSettingsGetMaximumContentWidthPerSheet.restype = ctypes.c_float
_lib.BridgeSpreadsheetSettingsGetMaximumContentWidthPerSheet.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetMaximumContentWidthPerSheetSingle.restype = None
_lib.BridgeSpreadsheetSettingsSetMaximumContentWidthPerSheetSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeSpreadsheetSettingsGetMaximumContentHeightPerSheet.restype = ctypes.c_float
_lib.BridgeSpreadsheetSettingsGetMaximumContentHeightPerSheet.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetMaximumContentHeightPerSheetSingle.restype = None
_lib.BridgeSpreadsheetSettingsSetMaximumContentHeightPerSheetSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeSpreadsheetSettingsGetMaximumPageWidth.restype = ctypes.c_float
_lib.BridgeSpreadsheetSettingsGetMaximumPageWidth.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetMaximumPageWidthSingle.restype = None
_lib.BridgeSpreadsheetSettingsSetMaximumPageWidthSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]

_lib.BridgeSpreadsheetSettingsGetMaximumPageHeight.restype = ctypes.c_float
_lib.BridgeSpreadsheetSettingsGetMaximumPageHeight.argtypes = [ctypes.c_void_p]

_lib.BridgeSpreadsheetSettingsSetMaximumPageHeightSingle.restype = None
_lib.BridgeSpreadsheetSettingsSetMaximumPageHeightSingle.argtypes = [ctypes.c_void_p, ctypes.c_float]


class SpreadsheetSettings:
    """
    Merged view of SpreadsheetSettings, combining immutable defaults, SDK overrides, and document overrides. Property writes automatically target the appropriate level (document if available, otherwise SDK).
    """

    def __init__(self):
        """Cannot instantiate SpreadsheetSettings directly. Use static factory methods instead."""
        raise TypeError("SpreadsheetSettings cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgeSpreadsheetSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSpreadsheetSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSpreadsheetSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SpreadsheetSettingsError(f"SpreadsheetSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("SpreadsheetSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_split_sheets_into_pages(self) -> bool:
        """
        Gets the SplitSheetsIntoPages property.

        Returns:
            bool: The value of the SplitSheetsIntoPages property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetSplitSheetsIntoPages(self._handle)
        self._check_error()
        return result

    def set_split_sheets_into_pages(self, value: bool) -> None:
        """
        Sets the SplitSheetsIntoPages property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetSplitSheetsIntoPagesBoolean(self._handle, value)
        self._check_error()

    def get_render_sheet_headers_and_footers(self) -> bool:
        """
        Gets the RenderSheetHeadersAndFooters property.

        Returns:
            bool: The value of the RenderSheetHeadersAndFooters property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetRenderSheetHeadersAndFooters(self._handle)
        self._check_error()
        return result

    def set_render_sheet_headers_and_footers(self, value: bool) -> None:
        """
        Sets the RenderSheetHeadersAndFooters property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetRenderSheetHeadersAndFootersBoolean(self._handle, value)
        self._check_error()

    def get_render_only_print_area(self) -> bool:
        """
        Gets the RenderOnlyPrintArea property.

        Returns:
            bool: The value of the RenderOnlyPrintArea property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetRenderOnlyPrintArea(self._handle)
        self._check_error()
        return result

    def set_render_only_print_area(self, value: bool) -> None:
        """
        Sets the RenderOnlyPrintArea property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetRenderOnlyPrintAreaBoolean(self._handle, value)
        self._check_error()

    def get_half_transparent_header_footer(self) -> bool:
        """
        Gets the HalfTransparentHeaderFooter property.

        Returns:
            bool: The value of the HalfTransparentHeaderFooter property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetHalfTransparentHeaderFooter(self._handle)
        self._check_error()
        return result

    def set_half_transparent_header_footer(self, value: bool) -> None:
        """
        Sets the HalfTransparentHeaderFooter property.

        Args:
            value (bool)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetHalfTransparentHeaderFooterBoolean(self._handle, value)
        self._check_error()

    def get_page_height_override(self) -> float:
        """
        Gets the PageHeightOverride property.

        Returns:
            float: The value of the PageHeightOverride property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetPageHeightOverride(self._handle)
        self._check_error()
        return result

    def set_page_height_override(self, value: float) -> None:
        """
        Sets the PageHeightOverride property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetPageHeightOverrideSingle(self._handle, value)
        self._check_error()

    def get_page_width_override(self) -> float:
        """
        Gets the PageWidthOverride property.

        Returns:
            float: The value of the PageWidthOverride property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetPageWidthOverride(self._handle)
        self._check_error()
        return result

    def set_page_width_override(self, value: float) -> None:
        """
        Sets the PageWidthOverride property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetPageWidthOverrideSingle(self._handle, value)
        self._check_error()

    def get_left_margin_override(self) -> float:
        """
        Gets the LeftMarginOverride property.

        Returns:
            float: The value of the LeftMarginOverride property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetLeftMarginOverride(self._handle)
        self._check_error()
        return result

    def set_left_margin_override(self, value: float) -> None:
        """
        Sets the LeftMarginOverride property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetLeftMarginOverrideSingle(self._handle, value)
        self._check_error()

    def get_top_margin_override(self) -> float:
        """
        Gets the TopMarginOverride property.

        Returns:
            float: The value of the TopMarginOverride property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetTopMarginOverride(self._handle)
        self._check_error()
        return result

    def set_top_margin_override(self, value: float) -> None:
        """
        Sets the TopMarginOverride property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetTopMarginOverrideSingle(self._handle, value)
        self._check_error()

    def get_right_margin_override(self) -> float:
        """
        Gets the RightMarginOverride property.

        Returns:
            float: The value of the RightMarginOverride property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetRightMarginOverride(self._handle)
        self._check_error()
        return result

    def set_right_margin_override(self, value: float) -> None:
        """
        Sets the RightMarginOverride property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetRightMarginOverrideSingle(self._handle, value)
        self._check_error()

    def get_bottom_margin_override(self) -> float:
        """
        Gets the BottomMarginOverride property.

        Returns:
            float: The value of the BottomMarginOverride property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetBottomMarginOverride(self._handle)
        self._check_error()
        return result

    def set_bottom_margin_override(self, value: float) -> None:
        """
        Sets the BottomMarginOverride property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetBottomMarginOverrideSingle(self._handle, value)
        self._check_error()

    def get_maximum_content_width_per_sheet(self) -> float:
        """
        Gets the MaximumContentWidthPerSheet property.

        Returns:
            float: The value of the MaximumContentWidthPerSheet property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetMaximumContentWidthPerSheet(self._handle)
        self._check_error()
        return result

    def set_maximum_content_width_per_sheet(self, value: float) -> None:
        """
        Sets the MaximumContentWidthPerSheet property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetMaximumContentWidthPerSheetSingle(self._handle, value)
        self._check_error()

    def get_maximum_content_height_per_sheet(self) -> float:
        """
        Gets the MaximumContentHeightPerSheet property.

        Returns:
            float: The value of the MaximumContentHeightPerSheet property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetMaximumContentHeightPerSheet(self._handle)
        self._check_error()
        return result

    def set_maximum_content_height_per_sheet(self, value: float) -> None:
        """
        Sets the MaximumContentHeightPerSheet property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetMaximumContentHeightPerSheetSingle(self._handle, value)
        self._check_error()

    def get_maximum_page_width(self) -> float:
        """
        Gets the MaximumPageWidth property.

        Returns:
            float: The value of the MaximumPageWidth property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetMaximumPageWidth(self._handle)
        self._check_error()
        return result

    def set_maximum_page_width(self, value: float) -> None:
        """
        Sets the MaximumPageWidth property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetMaximumPageWidthSingle(self._handle, value)
        self._check_error()

    def get_maximum_page_height(self) -> float:
        """
        Gets the MaximumPageHeight property.

        Returns:
            float: The value of the MaximumPageHeight property.

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeSpreadsheetSettingsGetMaximumPageHeight(self._handle)
        self._check_error()
        return result

    def set_maximum_page_height(self, value: float) -> None:
        """
        Sets the MaximumPageHeight property.

        Args:
            value (float)

        Returns:
            None: The result of the operation

        Raises:
            SpreadsheetSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSpreadsheetSettingsSetMaximumPageHeightSingle(self._handle, value)
        self._check_error()

    @property
    def split_sheets_into_pages(self) -> bool:
        """
        Gets the SplitSheetsIntoPages property.

        Returns:
            bool: The value of the SplitSheetsIntoPages property.
        """
        return self.get_split_sheets_into_pages()

    @split_sheets_into_pages.setter
    def split_sheets_into_pages(self, value: bool) -> None:
        """
        Sets the split sheets into pages.

        Args:
            value (bool): The value to set.
        """
        self.set_split_sheets_into_pages(value)

    @property
    def render_sheet_headers_and_footers(self) -> bool:
        """
        Gets the RenderSheetHeadersAndFooters property.

        Returns:
            bool: The value of the RenderSheetHeadersAndFooters property.
        """
        return self.get_render_sheet_headers_and_footers()

    @render_sheet_headers_and_footers.setter
    def render_sheet_headers_and_footers(self, value: bool) -> None:
        """
        Sets the render sheet headers and footers.

        Args:
            value (bool): The value to set.
        """
        self.set_render_sheet_headers_and_footers(value)

    @property
    def render_only_print_area(self) -> bool:
        """
        Gets the RenderOnlyPrintArea property.

        Returns:
            bool: The value of the RenderOnlyPrintArea property.
        """
        return self.get_render_only_print_area()

    @render_only_print_area.setter
    def render_only_print_area(self, value: bool) -> None:
        """
        Sets the render only print area.

        Args:
            value (bool): The value to set.
        """
        self.set_render_only_print_area(value)

    @property
    def half_transparent_header_footer(self) -> bool:
        """
        Gets the HalfTransparentHeaderFooter property.

        Returns:
            bool: The value of the HalfTransparentHeaderFooter property.
        """
        return self.get_half_transparent_header_footer()

    @half_transparent_header_footer.setter
    def half_transparent_header_footer(self, value: bool) -> None:
        """
        Sets the half transparent header footer.

        Args:
            value (bool): The value to set.
        """
        self.set_half_transparent_header_footer(value)

    @property
    def page_height_override(self) -> float:
        """
        Gets the PageHeightOverride property.

        Returns:
            float: The value of the PageHeightOverride property.
        """
        return self.get_page_height_override()

    @page_height_override.setter
    def page_height_override(self, value: float) -> None:
        """
        Sets the page height override.

        Args:
            value (float): The value to set.
        """
        self.set_page_height_override(value)

    @property
    def page_width_override(self) -> float:
        """
        Gets the PageWidthOverride property.

        Returns:
            float: The value of the PageWidthOverride property.
        """
        return self.get_page_width_override()

    @page_width_override.setter
    def page_width_override(self, value: float) -> None:
        """
        Sets the page width override.

        Args:
            value (float): The value to set.
        """
        self.set_page_width_override(value)

    @property
    def left_margin_override(self) -> float:
        """
        Gets the LeftMarginOverride property.

        Returns:
            float: The value of the LeftMarginOverride property.
        """
        return self.get_left_margin_override()

    @left_margin_override.setter
    def left_margin_override(self, value: float) -> None:
        """
        Sets the left margin override.

        Args:
            value (float): The value to set.
        """
        self.set_left_margin_override(value)

    @property
    def top_margin_override(self) -> float:
        """
        Gets the TopMarginOverride property.

        Returns:
            float: The value of the TopMarginOverride property.
        """
        return self.get_top_margin_override()

    @top_margin_override.setter
    def top_margin_override(self, value: float) -> None:
        """
        Sets the top margin override.

        Args:
            value (float): The value to set.
        """
        self.set_top_margin_override(value)

    @property
    def right_margin_override(self) -> float:
        """
        Gets the RightMarginOverride property.

        Returns:
            float: The value of the RightMarginOverride property.
        """
        return self.get_right_margin_override()

    @right_margin_override.setter
    def right_margin_override(self, value: float) -> None:
        """
        Sets the right margin override.

        Args:
            value (float): The value to set.
        """
        self.set_right_margin_override(value)

    @property
    def bottom_margin_override(self) -> float:
        """
        Gets the BottomMarginOverride property.

        Returns:
            float: The value of the BottomMarginOverride property.
        """
        return self.get_bottom_margin_override()

    @bottom_margin_override.setter
    def bottom_margin_override(self, value: float) -> None:
        """
        Sets the bottom margin override.

        Args:
            value (float): The value to set.
        """
        self.set_bottom_margin_override(value)

    @property
    def maximum_content_width_per_sheet(self) -> float:
        """
        Gets the MaximumContentWidthPerSheet property.

        Returns:
            float: The value of the MaximumContentWidthPerSheet property.
        """
        return self.get_maximum_content_width_per_sheet()

    @maximum_content_width_per_sheet.setter
    def maximum_content_width_per_sheet(self, value: float) -> None:
        """
        Sets the maximum content width per sheet.

        Args:
            value (float): The value to set.
        """
        self.set_maximum_content_width_per_sheet(value)

    @property
    def maximum_content_height_per_sheet(self) -> float:
        """
        Gets the MaximumContentHeightPerSheet property.

        Returns:
            float: The value of the MaximumContentHeightPerSheet property.
        """
        return self.get_maximum_content_height_per_sheet()

    @maximum_content_height_per_sheet.setter
    def maximum_content_height_per_sheet(self, value: float) -> None:
        """
        Sets the maximum content height per sheet.

        Args:
            value (float): The value to set.
        """
        self.set_maximum_content_height_per_sheet(value)

    @property
    def maximum_page_width(self) -> float:
        """
        Gets the MaximumPageWidth property.

        Returns:
            float: The value of the MaximumPageWidth property.
        """
        return self.get_maximum_page_width()

    @maximum_page_width.setter
    def maximum_page_width(self, value: float) -> None:
        """
        Sets the maximum page width.

        Args:
            value (float): The value to set.
        """
        self.set_maximum_page_width(value)

    @property
    def maximum_page_height(self) -> float:
        """
        Gets the MaximumPageHeight property.

        Returns:
            float: The value of the MaximumPageHeight property.
        """
        return self.get_maximum_page_height()

    @maximum_page_height.setter
    def maximum_page_height(self, value: float) -> None:
        """
        Sets the maximum page height.

        Args:
            value (float): The value to set.
        """
        self.set_maximum_page_height(value)



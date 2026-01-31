"""
Document module.
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


class DocumentError(Exception):
    """Exception raised by Document operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeDocumentInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeDocumentInitNSDKH.argtypes = []

_lib.BridgeDocumentCloseNSDKH.restype = None
_lib.BridgeDocumentCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeDocumentGetLastErrorCode.argtypes = []

_lib.BridgeDocumentGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeDocumentGetLastErrorMessage.argtypes = []

_lib.BridgeDocumentFreeErrorString.restype = None
_lib.BridgeDocumentFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentOpenString.restype = ctypes.c_void_p
_lib.BridgeDocumentOpenString.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentOpenStringDocumentSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentOpenStringDocumentSettings.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentExportStringIExporter.restype = None
_lib.BridgeDocumentExportStringIExporter.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentExportAsHtmlString.restype = None
_lib.BridgeDocumentExportAsHtmlString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentExportAsImageString.restype = None
_lib.BridgeDocumentExportAsImageString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentExportAsMarkdownString.restype = None
_lib.BridgeDocumentExportAsMarkdownString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentExportAsPdfString.restype = None
_lib.BridgeDocumentExportAsPdfString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentExportAsPresentationString.restype = None
_lib.BridgeDocumentExportAsPresentationString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentExportAsSpreadsheetString.restype = None
_lib.BridgeDocumentExportAsSpreadsheetString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentExportAsSvgString.restype = None
_lib.BridgeDocumentExportAsSvgString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentExportAsWordString.restype = None
_lib.BridgeDocumentExportAsWordString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentGetUnderlyingType.restype = ctypes.c_int32
_lib.BridgeDocumentGetUnderlyingType.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentGetSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentGetSettings.argtypes = [ctypes.c_void_p]


class Document:
    """
    Represents a document that can be opened, edited, and exported in various formats. Provides a unified interface for working with different document types including PDF, Word, Excel, and more.
    """

    def __init__(self):
        """Initialize a new Document instance."""
        self._handle = _lib.BridgeDocumentInitNSDKH()
        if not self._handle:
            self._check_error()
        self._closed = False

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        """Close and cleanup the native resources."""
        if not self._closed and self._handle:
            _lib.BridgeDocumentCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeDocumentGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeDocumentGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeDocumentFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise DocumentError(f"Document: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("Document instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    @staticmethod
    def _get_underlying_type_from_handle(handle):
        """
        Queries the UnderlyingType directly from a native handle without creating a wrapper instance.
        This is used by polymorphic collections to determine the correct subtype.
        """
        result = _lib.BridgeDocumentGetUnderlyingType(handle)
        error_code = _lib.BridgeDocumentGetLastErrorCode()
        if error_code != 0:
            return None
        return import_module('.documenttype', package=__package__).DocumentType(result)

    @classmethod
    def open(cls, file_path: str, settings: Optional['DocumentSettings'] = None) -> 'Document':
        """
        Opens a document from a file path using default settings.

        This method has multiple overloads. Arguments are resolved at runtime.

        Raises:
            DocumentError: If the operation fails
            TypeError: If no matching overload is found
        """

        _args = (file_path, settings)
        _overload_map = {
            ('str',): 'BridgeDocumentOpenString',
            ('str', 'DocumentSettings'): 'BridgeDocumentOpenStringDocumentSettings',
        }

        _bridge_func_name = sdk_helpers.resolve_overload(_overload_map, *_args)
        if _bridge_func_name is None:
            raise TypeError(sdk_helpers.format_overload_error('open', _overload_map, *_args))

        _bridge_func = getattr(_lib, _bridge_func_name)
        _call_args = []
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
        error_code = _lib.BridgeDocumentGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeDocumentGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeDocumentFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise DocumentError(f"Open: {message} (code: {error_code})")
        return import_module('.document', package=__package__).Document._from_handle(result)

    def export(self, filepath: str, exporter: Any) -> None:
        """
        Exports the document to a file using the specified exporter.

        Args:
            filepath (str)
            exporter (Any)

        Returns:
            None: The result of the operation

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentExportStringIExporter(self._handle, filepath.encode('utf-8') if filepath else None, exporter._handle if exporter else None)
        self._check_error()

    def export_as_html(self, filepath: str) -> None:
        """
        Exports the document as Html format to the specified file path.

        Args:
            filepath (str)

        Returns:
            None: The result of the operation

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentExportAsHtmlString(self._handle, filepath.encode('utf-8') if filepath else None)
        self._check_error()

    def export_as_image(self, filepath: str) -> None:
        """
        Exports the document as Image format to the specified file path.

        Args:
            filepath (str)

        Returns:
            None: The result of the operation

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentExportAsImageString(self._handle, filepath.encode('utf-8') if filepath else None)
        self._check_error()

    def export_as_markdown(self, filepath: str) -> None:
        """
        Exports the document as Markdown format to the specified file path.

        Args:
            filepath (str)

        Returns:
            None: The result of the operation

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentExportAsMarkdownString(self._handle, filepath.encode('utf-8') if filepath else None)
        self._check_error()

    def export_as_pdf(self, filepath: str) -> None:
        """
        Exports the document as Pdf format to the specified file path.

        Args:
            filepath (str)

        Returns:
            None: The result of the operation

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentExportAsPdfString(self._handle, filepath.encode('utf-8') if filepath else None)
        self._check_error()

    def export_as_presentation(self, filepath: str) -> None:
        """
        Exports the document as Presentation format to the specified file path.

        Args:
            filepath (str)

        Returns:
            None: The result of the operation

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentExportAsPresentationString(self._handle, filepath.encode('utf-8') if filepath else None)
        self._check_error()

    def export_as_spreadsheet(self, filepath: str) -> None:
        """
        Exports the document as Spreadsheet format to the specified file path.

        Args:
            filepath (str)

        Returns:
            None: The result of the operation

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentExportAsSpreadsheetString(self._handle, filepath.encode('utf-8') if filepath else None)
        self._check_error()

    def export_as_svg(self, filepath: str) -> None:
        """
        Exports the document as Svg format to the specified file path.

        Args:
            filepath (str)

        Returns:
            None: The result of the operation

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentExportAsSvgString(self._handle, filepath.encode('utf-8') if filepath else None)
        self._check_error()

    def export_as_word(self, filepath: str) -> None:
        """
        Exports the document as Word format to the specified file path.

        Args:
            filepath (str)

        Returns:
            None: The result of the operation

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentExportAsWordString(self._handle, filepath.encode('utf-8') if filepath else None)
        self._check_error()

    def get_underlying_type(self) -> Any:
        """
        Gets the underlying document type (PDF, Word, Excel, etc.) of the opened document.

        Returns:
            Any: The value of the UnderlyingType property.

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentGetUnderlyingType(self._handle)
        self._check_error()
        return result

    def get_settings(self) -> 'DocumentSettings':
        """
        Gets the settings associated with this document instance.

        Returns:
            'DocumentSettings': The value of the Settings property.

        Raises:
            DocumentError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentGetSettings(self._handle)
        self._check_error()
        return import_module('.documentsettings', package=__package__).DocumentSettings._from_handle(result)

    @property
    def underlying_type(self) -> Any:
        """
        Gets the underlying document type (PDF, Word, Excel, etc.) of the opened document.

        Returns:
            Any: The value of the UnderlyingType property.
        """
        return self.get_underlying_type()

    @property
    def settings(self) -> 'DocumentSettings':
        """
        Gets the settings associated with this document instance.

        Returns:
            'DocumentSettings': The value of the Settings property.
        """
        return self.get_settings()



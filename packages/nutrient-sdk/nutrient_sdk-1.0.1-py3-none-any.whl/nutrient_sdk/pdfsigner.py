"""
PdfSigner module.
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


class PdfSignerError(Exception):
    """Exception raised by PdfSigner operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfSignerInitNSDKH.restype = ctypes.c_void_p
_lib.BridgePdfSignerInitNSDKH.argtypes = []

_lib.BridgePdfSignerCloseNSDKH.restype = None
_lib.BridgePdfSignerCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSignerGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfSignerGetLastErrorCode.argtypes = []

_lib.BridgePdfSignerGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfSignerGetLastErrorMessage.argtypes = []

_lib.BridgePdfSignerFreeErrorString.restype = None
_lib.BridgePdfSignerFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfSignerSignStringStringDigitalSignatureOptions.restype = None
_lib.BridgePdfSignerSignStringStringDigitalSignatureOptions.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfSignerSignFieldStringStringStringDigitalSignatureOptionsSignatureAppearance.restype = None
_lib.BridgePdfSignerSignFieldStringStringStringDigitalSignatureOptionsSignatureAppearance.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]


class PdfSigner:
    """
    Provides functionality for signing PDF documents. Supports both digital signatures (with certificate) and electronic signatures (visual only).

    The class enables adding signatures to PDF documents: Digital signatures use PFX/P12 certificates to cryptographically sign the document.Electronic signatures add visual representation (image/text) without cryptographic signing. For PAdES-B compliance, use CAdES signature mode (the default). For PAdES-T compliance, configure a in the signature options.
    """

    def __init__(self):
        """Initialize a new PdfSigner instance."""
        self._handle = _lib.BridgePdfSignerInitNSDKH()
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
            _lib.BridgePdfSignerCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgePdfSignerGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfSignerGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfSignerFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfSignerError(f"PdfSigner: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfSigner instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def sign(self, input_path: str, output_path: str, options: 'DigitalSignatureOptions') -> None:
        """
        Applies an invisible digital signature to a PDF document.

        Args:
            input_path (str)
            output_path (str)
            options ('DigitalSignatureOptions')

        Returns:
            None: The result of the operation

        Raises:
            PdfSignerError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSignerSignStringStringDigitalSignatureOptions(self._handle, input_path.encode('utf-8') if input_path else None, output_path.encode('utf-8') if output_path else None, options._handle if options else None)
        self._check_error()

    def sign_field(self, input_path: str, output_path: str, field_name: str, options: 'DigitalSignatureOptions', appearance: 'SignatureAppearance') -> None:
        """
        Applies a signature to a PDF document using an existing signature field. Supports both digital signatures (with certificate) and electronic signatures (visual only).

        Args:
            input_path (str)
            output_path (str)
            field_name (str)
            options ('DigitalSignatureOptions')
            appearance ('SignatureAppearance')

        Returns:
            None: The result of the operation

        Raises:
            PdfSignerError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfSignerSignFieldStringStringStringDigitalSignatureOptionsSignatureAppearance(self._handle, input_path.encode('utf-8') if input_path else None, output_path.encode('utf-8') if output_path else None, field_name.encode('utf-8') if field_name else None, options._handle if options else None, appearance._handle if appearance else None)
        self._check_error()



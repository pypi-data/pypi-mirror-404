"""
DigitalSignatureOptions module.
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


class DigitalSignatureOptionsError(Exception):
    """Exception raised by DigitalSignatureOptions operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeDigitalSignatureOptionsInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeDigitalSignatureOptionsInitNSDKH.argtypes = []

_lib.BridgeDigitalSignatureOptionsCloseNSDKH.restype = None
_lib.BridgeDigitalSignatureOptionsCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeDigitalSignatureOptionsGetLastErrorCode.argtypes = []

_lib.BridgeDigitalSignatureOptionsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeDigitalSignatureOptionsGetLastErrorMessage.argtypes = []

_lib.BridgeDigitalSignatureOptionsFreeErrorString.restype = None
_lib.BridgeDigitalSignatureOptionsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsGetCertificatePath.restype = ctypes.c_void_p
_lib.BridgeDigitalSignatureOptionsGetCertificatePath.argtypes = [ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsSetCertificatePathString.restype = None
_lib.BridgeDigitalSignatureOptionsSetCertificatePathString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsGetCertificatePassword.restype = ctypes.c_void_p
_lib.BridgeDigitalSignatureOptionsGetCertificatePassword.argtypes = [ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsSetCertificatePasswordString.restype = None
_lib.BridgeDigitalSignatureOptionsSetCertificatePasswordString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsGetSignerName.restype = ctypes.c_void_p
_lib.BridgeDigitalSignatureOptionsGetSignerName.argtypes = [ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsSetSignerNameString.restype = None
_lib.BridgeDigitalSignatureOptionsSetSignerNameString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsGetReason.restype = ctypes.c_void_p
_lib.BridgeDigitalSignatureOptionsGetReason.argtypes = [ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsSetReasonString.restype = None
_lib.BridgeDigitalSignatureOptionsSetReasonString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsGetLocation.restype = ctypes.c_void_p
_lib.BridgeDigitalSignatureOptionsGetLocation.argtypes = [ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsSetLocationString.restype = None
_lib.BridgeDigitalSignatureOptionsSetLocationString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsGetContactInfo.restype = ctypes.c_void_p
_lib.BridgeDigitalSignatureOptionsGetContactInfo.argtypes = [ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsSetContactInfoString.restype = None
_lib.BridgeDigitalSignatureOptionsSetContactInfoString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsGetHashAlgorithm.restype = ctypes.c_int32
_lib.BridgeDigitalSignatureOptionsGetHashAlgorithm.argtypes = [ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsSetHashAlgorithmSignatureHashAlgorithm.restype = None
_lib.BridgeDigitalSignatureOptionsSetHashAlgorithmSignatureHashAlgorithm.argtypes = [ctypes.c_void_p, ctypes.c_int32]

_lib.BridgeDigitalSignatureOptionsGetTimestamp.restype = ctypes.c_void_p
_lib.BridgeDigitalSignatureOptionsGetTimestamp.argtypes = [ctypes.c_void_p]

_lib.BridgeDigitalSignatureOptionsSetTimestampTimestampConfiguration.restype = None
_lib.BridgeDigitalSignatureOptionsSetTimestampTimestampConfiguration.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


class DigitalSignatureOptions:
    """
    Options for creating a digital signature on a PDF document.

    A digital signature requires a certificate (PFX/P12 file) to cryptographically sign the document. Additional metadata such as signer name, reason, and location can optionally be included. For PAdES-T compliance, configure a to include a trusted timestamp.
    """

    def __init__(self):
        """Initialize a new DigitalSignatureOptions instance."""
        self._handle = _lib.BridgeDigitalSignatureOptionsInitNSDKH()
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
            _lib.BridgeDigitalSignatureOptionsCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeDigitalSignatureOptionsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeDigitalSignatureOptionsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeDigitalSignatureOptionsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise DigitalSignatureOptionsError(f"DigitalSignatureOptions: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("DigitalSignatureOptions instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_certificate_path(self) -> str:
        """
        Gets the file path to the PFX/P12 certificate file.

        Returns:
            str: The value of the CertificatePath property.

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDigitalSignatureOptionsGetCertificatePath(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_certificate_path(self, value: str) -> None:
        """
        Sets the file path to the PFX/P12 certificate file.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDigitalSignatureOptionsSetCertificatePathString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_certificate_password(self) -> str:
        """
        Gets the password to decrypt the PFX/P12 certificate file.

        Returns:
            str: The value of the CertificatePassword property.

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDigitalSignatureOptionsGetCertificatePassword(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_certificate_password(self, value: str) -> None:
        """
        Sets the password to decrypt the PFX/P12 certificate file.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDigitalSignatureOptionsSetCertificatePasswordString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_signer_name(self) -> str:
        """
        Gets the name of the person or entity signing the document.

        Returns:
            str: The value of the SignerName property.

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDigitalSignatureOptionsGetSignerName(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_signer_name(self, value: str) -> None:
        """
        Sets the name of the person or entity signing the document.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDigitalSignatureOptionsSetSignerNameString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_reason(self) -> str:
        """
        Gets the reason for signing the document.

        Returns:
            str: The value of the Reason property.

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDigitalSignatureOptionsGetReason(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_reason(self, value: str) -> None:
        """
        Sets the reason for signing the document.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDigitalSignatureOptionsSetReasonString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_location(self) -> str:
        """
        Gets the location where the document was signed.

        Returns:
            str: The value of the Location property.

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDigitalSignatureOptionsGetLocation(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_location(self, value: str) -> None:
        """
        Sets the location where the document was signed.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDigitalSignatureOptionsSetLocationString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_contact_info(self) -> str:
        """
        Gets contact information for the signer.

        Returns:
            str: The value of the ContactInfo property.

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDigitalSignatureOptionsGetContactInfo(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_contact_info(self, value: str) -> None:
        """
        Sets contact information for the signer.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDigitalSignatureOptionsSetContactInfoString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_hash_algorithm(self) -> Any:
        """
        Gets the hash algorithm to use for the signature.

        Returns:
            Any: The value of the HashAlgorithm property.

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDigitalSignatureOptionsGetHashAlgorithm(self._handle)
        self._check_error()
        return result

    def set_hash_algorithm(self, value: Any) -> None:
        """
        Sets the hash algorithm to use for the signature.

        Args:
            value (Any)

        Returns:
            None: The result of the operation

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDigitalSignatureOptionsSetHashAlgorithmSignatureHashAlgorithm(self._handle, value.value if isinstance(value, Enum) else value)
        self._check_error()

    def get_timestamp(self) -> 'TimestampConfiguration':
        """
        Gets optional timestamp configuration for PAdES-T compliance.

        Returns:
            'TimestampConfiguration': The value of the Timestamp property.

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDigitalSignatureOptionsGetTimestamp(self._handle)
        self._check_error()
        return import_module('.timestampconfiguration', package=__package__).TimestampConfiguration._from_handle(result)

    def set_timestamp(self, value: 'TimestampConfiguration') -> None:
        """
        Sets optional timestamp configuration for PAdES-T compliance.

        Args:
            value ('TimestampConfiguration')

        Returns:
            None: The result of the operation

        Raises:
            DigitalSignatureOptionsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDigitalSignatureOptionsSetTimestampTimestampConfiguration(self._handle, value._handle if value else None)
        self._check_error()

    @property
    def certificate_path(self) -> str:
        """
        Gets the file path to the PFX/P12 certificate file.

        Returns:
            str: The value of the CertificatePath property.
        """
        return self.get_certificate_path()

    @certificate_path.setter
    def certificate_path(self, value: str) -> None:
        """
        Sets the certificate path.

        Args:
            value (str): The value to set.
        """
        self.set_certificate_path(value)

    @property
    def certificate_password(self) -> str:
        """
        Gets the password to decrypt the PFX/P12 certificate file.

        Returns:
            str: The value of the CertificatePassword property.
        """
        return self.get_certificate_password()

    @certificate_password.setter
    def certificate_password(self, value: str) -> None:
        """
        Sets the certificate password.

        Args:
            value (str): The value to set.
        """
        self.set_certificate_password(value)

    @property
    def signer_name(self) -> str:
        """
        Gets the name of the person or entity signing the document.

        Returns:
            str: The value of the SignerName property.
        """
        return self.get_signer_name()

    @signer_name.setter
    def signer_name(self, value: str) -> None:
        """
        Sets the signer name.

        Args:
            value (str): The value to set.
        """
        self.set_signer_name(value)

    @property
    def reason(self) -> str:
        """
        Gets the reason for signing the document.

        Returns:
            str: The value of the Reason property.
        """
        return self.get_reason()

    @reason.setter
    def reason(self, value: str) -> None:
        """
        Sets the reason.

        Args:
            value (str): The value to set.
        """
        self.set_reason(value)

    @property
    def location(self) -> str:
        """
        Gets the location where the document was signed.

        Returns:
            str: The value of the Location property.
        """
        return self.get_location()

    @location.setter
    def location(self, value: str) -> None:
        """
        Sets the location.

        Args:
            value (str): The value to set.
        """
        self.set_location(value)

    @property
    def contact_info(self) -> str:
        """
        Gets contact information for the signer.

        Returns:
            str: The value of the ContactInfo property.
        """
        return self.get_contact_info()

    @contact_info.setter
    def contact_info(self, value: str) -> None:
        """
        Sets the contact info.

        Args:
            value (str): The value to set.
        """
        self.set_contact_info(value)

    @property
    def hash_algorithm(self) -> Any:
        """
        Gets the hash algorithm to use for the signature.

        Returns:
            Any: The value of the HashAlgorithm property.
        """
        return self.get_hash_algorithm()

    @hash_algorithm.setter
    def hash_algorithm(self, value: Any) -> None:
        """
        Sets the hash algorithm.

        Args:
            value (Any): The value to set.
        """
        self.set_hash_algorithm(value)

    @property
    def timestamp(self) -> 'TimestampConfiguration':
        """
        Gets optional timestamp configuration for PAdES-T compliance.

        Returns:
            'TimestampConfiguration': The value of the Timestamp property.
        """
        return self.get_timestamp()

    @timestamp.setter
    def timestamp(self, value: 'TimestampConfiguration') -> None:
        """
        Sets the timestamp.

        Args:
            value ('TimestampConfiguration'): The value to set.
        """
        self.set_timestamp(value)



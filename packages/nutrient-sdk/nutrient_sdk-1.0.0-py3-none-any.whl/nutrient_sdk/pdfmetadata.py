"""
PdfMetadata module.
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


class PdfMetadataError(Exception):
    """Exception raised by PdfMetadata operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgePdfMetadataGetLastErrorCode.restype = ctypes.c_int
_lib.BridgePdfMetadataGetLastErrorCode.argtypes = []

_lib.BridgePdfMetadataGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetLastErrorMessage.argtypes = []

_lib.BridgePdfMetadataFreeErrorString.restype = None
_lib.BridgePdfMetadataFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgePdfMetadataGetAuthor.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetAuthor.argtypes = [ctypes.c_void_p]

_lib.BridgePdfMetadataSetAuthorString.restype = None
_lib.BridgePdfMetadataSetAuthorString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfMetadataGetCreator.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetCreator.argtypes = [ctypes.c_void_p]

_lib.BridgePdfMetadataSetCreatorString.restype = None
_lib.BridgePdfMetadataSetCreatorString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfMetadataGetProducer.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetProducer.argtypes = [ctypes.c_void_p]

_lib.BridgePdfMetadataSetProducerString.restype = None
_lib.BridgePdfMetadataSetProducerString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfMetadataGetSubject.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetSubject.argtypes = [ctypes.c_void_p]

_lib.BridgePdfMetadataSetSubjectString.restype = None
_lib.BridgePdfMetadataSetSubjectString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfMetadataGetTitle.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetTitle.argtypes = [ctypes.c_void_p]

_lib.BridgePdfMetadataSetTitleString.restype = None
_lib.BridgePdfMetadataSetTitleString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfMetadataGetCreationDate.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetCreationDate.argtypes = [ctypes.c_void_p]

_lib.BridgePdfMetadataGetModificationDate.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetModificationDate.argtypes = [ctypes.c_void_p]

_lib.BridgePdfMetadataGetKeywords.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetKeywords.argtypes = [ctypes.c_void_p]

_lib.BridgePdfMetadataSetKeywordsString.restype = None
_lib.BridgePdfMetadataSetKeywordsString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfMetadataGetXMP.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetXMP.argtypes = [ctypes.c_void_p]

_lib.BridgePdfMetadataSetXMPString.restype = None
_lib.BridgePdfMetadataSetXMPString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfMetadataGetCustomPDFInformationString.restype = ctypes.c_void_p
_lib.BridgePdfMetadataGetCustomPDFInformationString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgePdfMetadataSetCustomPDFInformationStringString.restype = None
_lib.BridgePdfMetadataSetCustomPDFInformationStringString.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]


class PdfMetadata:
    """
    Provides access to PDF document metadata properties including standard document information dictionary fields and XMP metadata.

    This class allows reading and writing of standard PDF metadata fields such as title, author, subject, and keywords, as well as custom metadata properties. All changes to metadata properties are immediately applied to the underlying PDF document.
    """

    def __init__(self):
        """Cannot instantiate PdfMetadata directly. Use static factory methods instead."""
        raise TypeError("PdfMetadata cannot be instantiated directly. Use static factory methods to obtain instances.")

    def _check_error(self):
        error_code = _lib.BridgePdfMetadataGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgePdfMetadataGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgePdfMetadataFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise PdfMetadataError(f"PdfMetadata: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("PdfMetadata instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def get_author(self) -> str:
        """
        Gets the name of the person that created the document.

        Returns:
            str: The value of the Author property.

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfMetadataGetAuthor(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_author(self, value: str) -> None:
        """
        Sets the name of the person that created the document.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfMetadataSetAuthorString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_creator(self) -> str:
        """
        Gets the name of the application that created the original document.

        Returns:
            str: The value of the Creator property.

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfMetadataGetCreator(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_creator(self, value: str) -> None:
        """
        Sets the name of the application that created the original document.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfMetadataSetCreatorString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_producer(self) -> str:
        """
        Gets the name of the application that converted the document to PDF.

        Returns:
            str: The value of the Producer property.

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfMetadataGetProducer(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_producer(self, value: str) -> None:
        """
        Sets the name of the application that converted the document to PDF.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfMetadataSetProducerString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_subject(self) -> str:
        """
        Gets the subject of the document.

        Returns:
            str: The value of the Subject property.

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfMetadataGetSubject(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_subject(self, value: str) -> None:
        """
        Sets the subject of the document.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfMetadataSetSubjectString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_title(self) -> str:
        """
        Gets the title of the document.

        Returns:
            str: The value of the Title property.

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfMetadataGetTitle(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_title(self, value: str) -> None:
        """
        Sets the title of the document.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfMetadataSetTitleString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_creation_date(self) -> str:
        """
        Gets the date and time the document was created.

        Returns:
            str: The value of the CreationDate property.

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfMetadataGetCreationDate(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_modification_date(self) -> str:
        """
        Gets the date and time the document was most recently modified.

        Returns:
            str: The value of the ModificationDate property.

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfMetadataGetModificationDate(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def get_keywords(self) -> str:
        """
        Gets the keywords associated with the document.

        Returns:
            str: The value of the Keywords property.

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfMetadataGetKeywords(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_keywords(self, value: str) -> None:
        """
        Sets the keywords associated with the document.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfMetadataSetKeywordsString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_xmp(self) -> str:
        """
        Gets the XMP metadata stream of the document.

        Returns:
            str: The value of the XMP property.

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfMetadataGetXMP(self._handle)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_xmp(self, value: str) -> None:
        """
        Sets the XMP metadata stream of the document.

        Args:
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfMetadataSetXMPString(self._handle, value.encode('utf-8') if value else None)
        self._check_error()

    def get_custom_pdf_information(self, key: str) -> str:
        """
        Gets the value of a custom metadata property from the document information dictionary.

        Args:
            key (str)

        Returns:
            str: The value of the custom property as a string. Returns an empty string if the property does not exist.

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgePdfMetadataGetCustomPDFInformationString(self._handle, key.encode('utf-8') if key else None)
        self._check_error()
        return sdk_loader.convert_string_handle(result)

    def set_custom_pdf_information(self, key: str, value: str) -> None:
        """
        Sets the value of a custom metadata property in the document information dictionary.

        Args:
            key (str)
            value (str)

        Returns:
            None: The result of the operation

        Raises:
            PdfMetadataError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgePdfMetadataSetCustomPDFInformationStringString(self._handle, key.encode('utf-8') if key else None, value.encode('utf-8') if value else None)
        self._check_error()

    @property
    def author(self) -> str:
        """
        Gets the name of the person that created the document.

        Returns:
            str: The value of the Author property.
        """
        return self.get_author()

    @author.setter
    def author(self, value: str) -> None:
        """
        Sets the author.

        Args:
            value (str): The value to set.
        """
        self.set_author(value)

    @property
    def creator(self) -> str:
        """
        Gets the name of the application that created the original document.

        Returns:
            str: The value of the Creator property.
        """
        return self.get_creator()

    @creator.setter
    def creator(self, value: str) -> None:
        """
        Sets the creator.

        Args:
            value (str): The value to set.
        """
        self.set_creator(value)

    @property
    def producer(self) -> str:
        """
        Gets the name of the application that converted the document to PDF.

        Returns:
            str: The value of the Producer property.
        """
        return self.get_producer()

    @producer.setter
    def producer(self, value: str) -> None:
        """
        Sets the producer.

        Args:
            value (str): The value to set.
        """
        self.set_producer(value)

    @property
    def subject(self) -> str:
        """
        Gets the subject of the document.

        Returns:
            str: The value of the Subject property.
        """
        return self.get_subject()

    @subject.setter
    def subject(self, value: str) -> None:
        """
        Sets the subject.

        Args:
            value (str): The value to set.
        """
        self.set_subject(value)

    @property
    def title(self) -> str:
        """
        Gets the title of the document.

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
    def creation_date(self) -> str:
        """
        Gets the date and time the document was created.

        Returns:
            str: The value of the CreationDate property.
        """
        return self.get_creation_date()

    @property
    def modification_date(self) -> str:
        """
        Gets the date and time the document was most recently modified.

        Returns:
            str: The value of the ModificationDate property.
        """
        return self.get_modification_date()

    @property
    def keywords(self) -> str:
        """
        Gets the keywords associated with the document.

        Returns:
            str: The value of the Keywords property.
        """
        return self.get_keywords()

    @keywords.setter
    def keywords(self, value: str) -> None:
        """
        Sets the keywords.

        Args:
            value (str): The value to set.
        """
        self.set_keywords(value)

    @property
    def xmp(self) -> str:
        """
        Gets the XMP metadata stream of the document.

        Returns:
            str: The value of the XMP property.
        """
        return self.get_xmp()

    @xmp.setter
    def xmp(self, value: str) -> None:
        """
        Sets the xmp.

        Args:
            value (str): The value to set.
        """
        self.set_xmp(value)



"""
SdkSettings module.
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


class SdkSettingsError(Exception):
    """Exception raised by SdkSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeSdkSettingsInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsInitNSDKH.argtypes = []

_lib.BridgeSdkSettingsCloseNSDKH.restype = None
_lib.BridgeSdkSettingsCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeSdkSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeSdkSettingsGetLastErrorCode.argtypes = []

_lib.BridgeSdkSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeSdkSettingsFreeErrorString.restype = None
_lib.BridgeSdkSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeSdkSettingsLoadInstanceString.restype = None
_lib.BridgeSdkSettingsLoadInstanceString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeSdkSettingsExportInstanceString.restype = None
_lib.BridgeSdkSettingsExportInstanceString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeSdkSettingsLoadString.restype = None
_lib.BridgeSdkSettingsLoadString.argtypes = [ctypes.c_void_p]

_lib.BridgeSdkSettingsExportString.restype = None
_lib.BridgeSdkSettingsExportString.argtypes = [ctypes.c_void_p]

_lib.BridgeSdkSettingsGetAiAugmenterSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetAiAugmenterSettings.argtypes = []

_lib.BridgeSdkSettingsGetCadSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetCadSettings.argtypes = []

_lib.BridgeSdkSettingsGetClaudeApiSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetClaudeApiSettings.argtypes = []

_lib.BridgeSdkSettingsGetContentExtractionSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetContentExtractionSettings.argtypes = []

_lib.BridgeSdkSettingsGetConversionSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetConversionSettings.argtypes = []

_lib.BridgeSdkSettingsGetCustomVlmApiSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetCustomVlmApiSettings.argtypes = []

_lib.BridgeSdkSettingsGetDocumentLayoutJsonExportSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetDocumentLayoutJsonExportSettings.argtypes = []

_lib.BridgeSdkSettingsGetFinalizerSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetFinalizerSettings.argtypes = []

_lib.BridgeSdkSettingsGetHtmlSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetHtmlSettings.argtypes = []

_lib.BridgeSdkSettingsGetImageSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetImageSettings.argtypes = []

_lib.BridgeSdkSettingsGetInferenceLayoutSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetInferenceLayoutSettings.argtypes = []

_lib.BridgeSdkSettingsGetJbig2Settings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetJbig2Settings.argtypes = []

_lib.BridgeSdkSettingsGetJpegSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetJpegSettings.argtypes = []

_lib.BridgeSdkSettingsGetOcrSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetOcrSettings.argtypes = []

_lib.BridgeSdkSettingsGetOpenAIApiEndpointSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetOpenAIApiEndpointSettings.argtypes = []

_lib.BridgeSdkSettingsGetOpenAILanguagesDetectionSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetOpenAILanguagesDetectionSettings.argtypes = []

_lib.BridgeSdkSettingsGetOpenAIPictureAltSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetOpenAIPictureAltSettings.argtypes = []

_lib.BridgeSdkSettingsGetOpenSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetOpenSettings.argtypes = []

_lib.BridgeSdkSettingsGetPdfPageSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetPdfPageSettings.argtypes = []

_lib.BridgeSdkSettingsGetPdfSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetPdfSettings.argtypes = []

_lib.BridgeSdkSettingsGetPresentationSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetPresentationSettings.argtypes = []

_lib.BridgeSdkSettingsGetReadingOrderSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetReadingOrderSettings.argtypes = []

_lib.BridgeSdkSettingsGetSegmenterSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetSegmenterSettings.argtypes = []

_lib.BridgeSdkSettingsGetSpreadsheetSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetSpreadsheetSettings.argtypes = []

_lib.BridgeSdkSettingsGetTableRecognitionSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetTableRecognitionSettings.argtypes = []

_lib.BridgeSdkSettingsGetTiffSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetTiffSettings.argtypes = []

_lib.BridgeSdkSettingsGetVisionDescriptorSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetVisionDescriptorSettings.argtypes = []

_lib.BridgeSdkSettingsGetVisionSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetVisionSettings.argtypes = []

_lib.BridgeSdkSettingsGetWordsDetectionSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetWordsDetectionSettings.argtypes = []

_lib.BridgeSdkSettingsGetWordSettings.restype = ctypes.c_void_p
_lib.BridgeSdkSettingsGetWordSettings.argtypes = []


class SdkSettings:
    """
    Manages configuration settings for the Nutrient SDK. Provides functionality to load, export, and access various SDK settings through a type-safe registry system. This is a singleton class - use the static methods to access SDK settings.
    """

    def __init__(self):
        """Initialize a new SdkSettings instance."""
        self._handle = _lib.BridgeSdkSettingsInitNSDKH()
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
            _lib.BridgeSdkSettingsCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"SdkSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("SdkSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def load_instance(self, path: str) -> None:
        """
        Loads SDK settings from a JSON file.

        Args:
            path (str)

        Returns:
            None: The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSdkSettingsLoadInstanceString(self._handle, path.encode('utf-8') if path else None)
        self._check_error()

    def export_instance(self, path: str) -> None:
        """
        Exports the current SDK settings to a JSON file.

        Args:
            path (str)

        Returns:
            None: The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeSdkSettingsExportInstanceString(self._handle, path.encode('utf-8') if path else None)
        self._check_error()

    @classmethod
    def load(cls, path: str) -> None:
        """
        Static method to load SDK settings from a JSON file.

        Args:
            path (str)

        Returns:
            None: The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        _lib.BridgeSdkSettingsLoadString(path.encode('utf-8') if path else None)
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"Load: {message} (code: {error_code})")

    @classmethod
    def export(cls, path: str) -> None:
        """
        Static method to export the current SDK settings to a JSON file.

        Args:
            path (str)

        Returns:
            None: The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        _lib.BridgeSdkSettingsExportString(path.encode('utf-8') if path else None)
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"Export: {message} (code: {error_code})")

    @classmethod
    def get_ai_augmenter_settings(cls) -> 'AiAugmenterSettings':
        """
        Gets the settings for aiaugmenter.

        Returns:
            'AiAugmenterSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetAiAugmenterSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetAiAugmenterSettings: {message} (code: {error_code})")
        return import_module('.aiaugmentersettings', package=__package__).AiAugmenterSettings._from_handle(result)

    @classmethod
    def get_cad_settings(cls) -> 'CadSettings':
        """
        Gets the settings for CAD.

        Returns:
            'CadSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetCadSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetCadSettings: {message} (code: {error_code})")
        return import_module('.cadsettings', package=__package__).CadSettings._from_handle(result)

    @classmethod
    def get_claude_api_settings(cls) -> 'ClaudeApiSettings':
        """
        Gets the settings for claudeapi.

        Returns:
            'ClaudeApiSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetClaudeApiSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetClaudeApiSettings: {message} (code: {error_code})")
        return import_module('.claudeapisettings', package=__package__).ClaudeApiSettings._from_handle(result)

    @classmethod
    def get_content_extraction_settings(cls) -> 'ContentExtractionSettings':
        """
        Gets the settings for contentextraction.

        Returns:
            'ContentExtractionSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetContentExtractionSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetContentExtractionSettings: {message} (code: {error_code})")
        return import_module('.contentextractionsettings', package=__package__).ContentExtractionSettings._from_handle(result)

    @classmethod
    def get_conversion_settings(cls) -> 'ConversionSettings':
        """
        Gets the settings for conversion.

        Returns:
            'ConversionSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetConversionSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetConversionSettings: {message} (code: {error_code})")
        return import_module('.conversionsettings', package=__package__).ConversionSettings._from_handle(result)

    @classmethod
    def get_custom_vlm_api_settings(cls) -> 'CustomVlmApiSettings':
        """
        Gets the settings for customvlmapi.

        Returns:
            'CustomVlmApiSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetCustomVlmApiSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetCustomVlmApiSettings: {message} (code: {error_code})")
        return import_module('.customvlmapisettings', package=__package__).CustomVlmApiSettings._from_handle(result)

    @classmethod
    def get_document_layout_json_export_settings(cls) -> 'DocumentLayoutJsonExportSettings':
        """
        Gets the settings for documentlayoutjsonexport.

        Returns:
            'DocumentLayoutJsonExportSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetDocumentLayoutJsonExportSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetDocumentLayoutJsonExportSettings: {message} (code: {error_code})")
        return import_module('.documentlayoutjsonexportsettings', package=__package__).DocumentLayoutJsonExportSettings._from_handle(result)

    @classmethod
    def get_finalizer_settings(cls) -> 'FinalizerSettings':
        """
        Gets the settings for finalizer.

        Returns:
            'FinalizerSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetFinalizerSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetFinalizerSettings: {message} (code: {error_code})")
        return import_module('.finalizersettings', package=__package__).FinalizerSettings._from_handle(result)

    @classmethod
    def get_html_settings(cls) -> 'HtmlSettings':
        """
        Gets the settings for HTML.

        Returns:
            'HtmlSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetHtmlSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetHtmlSettings: {message} (code: {error_code})")
        return import_module('.htmlsettings', package=__package__).HtmlSettings._from_handle(result)

    @classmethod
    def get_image_settings(cls) -> 'ImageSettings':
        """
        Gets the settings for image.

        Returns:
            'ImageSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetImageSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetImageSettings: {message} (code: {error_code})")
        return import_module('.imagesettings', package=__package__).ImageSettings._from_handle(result)

    @classmethod
    def get_inference_layout_settings(cls) -> 'InferenceLayoutSettings':
        """
        Gets the settings for inferencelayout.

        Returns:
            'InferenceLayoutSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetInferenceLayoutSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetInferenceLayoutSettings: {message} (code: {error_code})")
        return import_module('.inferencelayoutsettings', package=__package__).InferenceLayoutSettings._from_handle(result)

    @classmethod
    def get_jbig2_settings(cls) -> 'Jbig2Settings':
        """
        Gets the settings for jbig2.

        Returns:
            'Jbig2Settings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetJbig2Settings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetJbig2Settings: {message} (code: {error_code})")
        return import_module('.jbig2settings', package=__package__).Jbig2Settings._from_handle(result)

    @classmethod
    def get_jpeg_settings(cls) -> 'JpegSettings':
        """
        Gets the settings for jpeg.

        Returns:
            'JpegSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetJpegSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetJpegSettings: {message} (code: {error_code})")
        return import_module('.jpegsettings', package=__package__).JpegSettings._from_handle(result)

    @classmethod
    def get_ocr_settings(cls) -> 'OcrSettings':
        """
        Gets the settings for ocr.

        Returns:
            'OcrSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetOcrSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetOcrSettings: {message} (code: {error_code})")
        return import_module('.ocrsettings', package=__package__).OcrSettings._from_handle(result)

    @classmethod
    def get_open_ai_api_endpoint_settings(cls) -> 'OpenAIApiEndpointSettings':
        """
        Gets the settings for openaiapiendpoint.

        Returns:
            'OpenAIApiEndpointSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetOpenAIApiEndpointSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetOpenAIApiEndpointSettings: {message} (code: {error_code})")
        return import_module('.openaiapiendpointsettings', package=__package__).OpenAIApiEndpointSettings._from_handle(result)

    @classmethod
    def get_open_ai_languages_detection_settings(cls) -> 'OpenAILanguagesDetectionSettings':
        """
        Gets the settings for openailanguagesdetection.

        Returns:
            'OpenAILanguagesDetectionSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetOpenAILanguagesDetectionSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetOpenAILanguagesDetectionSettings: {message} (code: {error_code})")
        return import_module('.openailanguagesdetectionsettings', package=__package__).OpenAILanguagesDetectionSettings._from_handle(result)

    @classmethod
    def get_open_ai_picture_alt_settings(cls) -> 'OpenAIPictureAltSettings':
        """
        Gets the settings for openaipicturealt.

        Returns:
            'OpenAIPictureAltSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetOpenAIPictureAltSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetOpenAIPictureAltSettings: {message} (code: {error_code})")
        return import_module('.openaipicturealtsettings', package=__package__).OpenAIPictureAltSettings._from_handle(result)

    @classmethod
    def get_open_settings(cls) -> 'OpenSettings':
        """
        Gets the settings for opening documents.

        Returns:
            'OpenSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetOpenSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetOpenSettings: {message} (code: {error_code})")
        return import_module('.opensettings', package=__package__).OpenSettings._from_handle(result)

    @classmethod
    def get_pdf_page_settings(cls) -> 'PdfPageSettings':
        """
        Gets the settings for PDF page.

        Returns:
            'PdfPageSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetPdfPageSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetPdfPageSettings: {message} (code: {error_code})")
        return import_module('.pdfpagesettings', package=__package__).PdfPageSettings._from_handle(result)

    @classmethod
    def get_pdf_settings(cls) -> 'PdfSettings':
        """
        Gets the settings for PDF.

        Returns:
            'PdfSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetPdfSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetPdfSettings: {message} (code: {error_code})")
        return import_module('.pdfsettings', package=__package__).PdfSettings._from_handle(result)

    @classmethod
    def get_presentation_settings(cls) -> 'PresentationSettings':
        """
        Gets the settings for presentation.

        Returns:
            'PresentationSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetPresentationSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetPresentationSettings: {message} (code: {error_code})")
        return import_module('.presentationsettings', package=__package__).PresentationSettings._from_handle(result)

    @classmethod
    def get_reading_order_settings(cls) -> 'ReadingOrderSettings':
        """
        Gets the settings for readingorder.

        Returns:
            'ReadingOrderSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetReadingOrderSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetReadingOrderSettings: {message} (code: {error_code})")
        return import_module('.readingordersettings', package=__package__).ReadingOrderSettings._from_handle(result)

    @classmethod
    def get_segmenter_settings(cls) -> 'SegmenterSettings':
        """
        Gets the settings for segmenter.

        Returns:
            'SegmenterSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetSegmenterSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetSegmenterSettings: {message} (code: {error_code})")
        return import_module('.segmentersettings', package=__package__).SegmenterSettings._from_handle(result)

    @classmethod
    def get_spreadsheet_settings(cls) -> 'SpreadsheetSettings':
        """
        Gets the settings for spreadsheet.

        Returns:
            'SpreadsheetSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetSpreadsheetSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetSpreadsheetSettings: {message} (code: {error_code})")
        return import_module('.spreadsheetsettings', package=__package__).SpreadsheetSettings._from_handle(result)

    @classmethod
    def get_table_recognition_settings(cls) -> 'TableRecognitionSettings':
        """
        Gets the settings for tablerecognition.

        Returns:
            'TableRecognitionSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetTableRecognitionSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetTableRecognitionSettings: {message} (code: {error_code})")
        return import_module('.tablerecognitionsettings', package=__package__).TableRecognitionSettings._from_handle(result)

    @classmethod
    def get_tiff_settings(cls) -> 'TiffSettings':
        """
        Gets the settings for tiff.

        Returns:
            'TiffSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetTiffSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetTiffSettings: {message} (code: {error_code})")
        return import_module('.tiffsettings', package=__package__).TiffSettings._from_handle(result)

    @classmethod
    def get_vision_descriptor_settings(cls) -> 'VisionDescriptorSettings':
        """
        Gets the settings for visiondescriptor.

        Returns:
            'VisionDescriptorSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetVisionDescriptorSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetVisionDescriptorSettings: {message} (code: {error_code})")
        return import_module('.visiondescriptorsettings', package=__package__).VisionDescriptorSettings._from_handle(result)

    @classmethod
    def get_vision_settings(cls) -> 'VisionSettings':
        """
        Gets the settings for vision.

        Returns:
            'VisionSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetVisionSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetVisionSettings: {message} (code: {error_code})")
        return import_module('.visionsettings', package=__package__).VisionSettings._from_handle(result)

    @classmethod
    def get_words_detection_settings(cls) -> 'WordsDetectionSettings':
        """
        Gets the settings for wordsdetection.

        Returns:
            'WordsDetectionSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetWordsDetectionSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetWordsDetectionSettings: {message} (code: {error_code})")
        return import_module('.wordsdetectionsettings', package=__package__).WordsDetectionSettings._from_handle(result)

    @classmethod
    def get_word_settings(cls) -> 'WordSettings':
        """
        Gets the settings for Word documents.

        Returns:
            'WordSettings': The result of the operation

        Raises:
            SdkSettingsError: If the operation fails
        """

        result = _lib.BridgeSdkSettingsGetWordSettings()
        error_code = _lib.BridgeSdkSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeSdkSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeSdkSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise SdkSettingsError(f"GetWordSettings: {message} (code: {error_code})")
        return import_module('.wordsettings', package=__package__).WordSettings._from_handle(result)



"""
DocumentSettings module.
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


class DocumentSettingsError(Exception):
    """Exception raised by DocumentSettings operations."""
    pass

class ErrorInfo(ctypes.Structure):
    """Structure to hold error information from native code."""
    _fields_ = [
        ("code", ctypes.c_int),
        ("message", ctypes.c_char * 1024),
        ("source", ctypes.c_char * 256)
    ]

_lib.BridgeDocumentSettingsInitNSDKH.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsInitNSDKH.argtypes = []

_lib.BridgeDocumentSettingsCloseNSDKH.restype = None
_lib.BridgeDocumentSettingsCloseNSDKH.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetLastErrorCode.restype = ctypes.c_int
_lib.BridgeDocumentSettingsGetLastErrorCode.argtypes = []

_lib.BridgeDocumentSettingsGetLastErrorMessage.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetLastErrorMessage.argtypes = []

_lib.BridgeDocumentSettingsFreeErrorString.restype = None
_lib.BridgeDocumentSettingsFreeErrorString.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsLoadString.restype = None
_lib.BridgeDocumentSettingsLoadString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentSettingsExportString.restype = None
_lib.BridgeDocumentSettingsExportString.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetWordSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetWordSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetTiffSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetTiffSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetSpreadsheetSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetSpreadsheetSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetPresentationSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetPresentationSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetPdfSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetPdfSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetPdfPageSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetPdfPageSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetOpenSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetOpenSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetOcrSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetOcrSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetJpegSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetJpegSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetJbig2Settings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetJbig2Settings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetImageSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetImageSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetHtmlSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetHtmlSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetDocumentLayoutJsonExportSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetDocumentLayoutJsonExportSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetWordsDetectionSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetWordsDetectionSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetVisionSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetVisionSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetVisionDescriptorSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetVisionDescriptorSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetTableRecognitionSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetTableRecognitionSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetSegmenterSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetSegmenterSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetReadingOrderSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetReadingOrderSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetOpenAIPictureAltSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetOpenAIPictureAltSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetOpenAILanguagesDetectionSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetOpenAILanguagesDetectionSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetInferenceLayoutSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetInferenceLayoutSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetFinalizerSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetFinalizerSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetContentExtractionSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetContentExtractionSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetOpenAIApiEndpointSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetOpenAIApiEndpointSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetCustomVlmApiSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetCustomVlmApiSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetClaudeApiSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetClaudeApiSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetAiAugmenterSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetAiAugmenterSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetConversionSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetConversionSettings.argtypes = [ctypes.c_void_p]

_lib.BridgeDocumentSettingsGetCadSettings.restype = ctypes.c_void_p
_lib.BridgeDocumentSettingsGetCadSettings.argtypes = [ctypes.c_void_p]


class DocumentSettings:
    """
    Provides configuration settings for SDK document operations. Manages document-level settings with overrides over SDK defaults.
    """

    def __init__(self):
        """Initialize a new DocumentSettings instance."""
        self._handle = _lib.BridgeDocumentSettingsInitNSDKH()
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
            _lib.BridgeDocumentSettingsCloseNSDKH(self._handle)
            self._handle = None
            self._closed = True

    def _check_error(self):
        error_code = _lib.BridgeDocumentSettingsGetLastErrorCode()
        if error_code != 0:
            message_ptr = _lib.BridgeDocumentSettingsGetLastErrorMessage()
            if message_ptr:
                message = ctypes.string_at(message_ptr).decode('utf-8')
                _lib.BridgeDocumentSettingsFreeErrorString(message_ptr)
            else:
                message = "Unknown error"
            raise DocumentSettingsError(f"DocumentSettings: {message} (code: {error_code})")
    
    def _ensure_not_closed(self):
        if self._closed:
            raise ValueError("DocumentSettings instance has been closed")

    @classmethod
    def _from_handle(cls, handle):
        if not handle:
            return None  # Null handle means object not found or null return
        instance = cls.__new__(cls)
        instance._handle = handle
        instance._closed = False
        return instance

    def load(self, path: str) -> None:
        """
        Loads document settings from a JSON file.

        Args:
            path (str)

        Returns:
            None: The result of the operation

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentSettingsLoadString(self._handle, path.encode('utf-8') if path else None)
        self._check_error()

    def export(self, path: str) -> None:
        """
        Exports the current document settings to a JSON file.

        Args:
            path (str)

        Returns:
            None: The result of the operation

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        _lib.BridgeDocumentSettingsExportString(self._handle, path.encode('utf-8') if path else None)
        self._check_error()

    def get_word_settings(self) -> 'WordSettings':
        """
        Gets the settings for Word documents.

        Returns:
            'WordSettings': The Word documents settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetWordSettings(self._handle)
        self._check_error()
        return import_module('.wordsettings', package=__package__).WordSettings._from_handle(result)

    def get_tiff_settings(self) -> 'TiffSettings':
        """
        Gets the settings for tiff.

        Returns:
            'TiffSettings': The tiff settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetTiffSettings(self._handle)
        self._check_error()
        return import_module('.tiffsettings', package=__package__).TiffSettings._from_handle(result)

    def get_spreadsheet_settings(self) -> 'SpreadsheetSettings':
        """
        Gets the settings for spreadsheet.

        Returns:
            'SpreadsheetSettings': The spreadsheet settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetSpreadsheetSettings(self._handle)
        self._check_error()
        return import_module('.spreadsheetsettings', package=__package__).SpreadsheetSettings._from_handle(result)

    def get_presentation_settings(self) -> 'PresentationSettings':
        """
        Gets the settings for presentation.

        Returns:
            'PresentationSettings': The presentation settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetPresentationSettings(self._handle)
        self._check_error()
        return import_module('.presentationsettings', package=__package__).PresentationSettings._from_handle(result)

    def get_pdf_settings(self) -> 'PdfSettings':
        """
        Gets the settings for PDF.

        Returns:
            'PdfSettings': The PDF settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetPdfSettings(self._handle)
        self._check_error()
        return import_module('.pdfsettings', package=__package__).PdfSettings._from_handle(result)

    def get_pdf_page_settings(self) -> 'PdfPageSettings':
        """
        Gets the settings for PDF page.

        Returns:
            'PdfPageSettings': The PDF page settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetPdfPageSettings(self._handle)
        self._check_error()
        return import_module('.pdfpagesettings', package=__package__).PdfPageSettings._from_handle(result)

    def get_open_settings(self) -> 'OpenSettings':
        """
        Gets the settings for opening documents.

        Returns:
            'OpenSettings': The opening documents settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetOpenSettings(self._handle)
        self._check_error()
        return import_module('.opensettings', package=__package__).OpenSettings._from_handle(result)

    def get_ocr_settings(self) -> 'OcrSettings':
        """
        Gets the settings for ocr.

        Returns:
            'OcrSettings': The ocr settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetOcrSettings(self._handle)
        self._check_error()
        return import_module('.ocrsettings', package=__package__).OcrSettings._from_handle(result)

    def get_jpeg_settings(self) -> 'JpegSettings':
        """
        Gets the settings for jpeg.

        Returns:
            'JpegSettings': The jpeg settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetJpegSettings(self._handle)
        self._check_error()
        return import_module('.jpegsettings', package=__package__).JpegSettings._from_handle(result)

    def get_jbig2_settings(self) -> 'Jbig2Settings':
        """
        Gets the settings for jbig2.

        Returns:
            'Jbig2Settings': The jbig2 settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetJbig2Settings(self._handle)
        self._check_error()
        return import_module('.jbig2settings', package=__package__).Jbig2Settings._from_handle(result)

    def get_image_settings(self) -> 'ImageSettings':
        """
        Gets the settings for image.

        Returns:
            'ImageSettings': The image settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetImageSettings(self._handle)
        self._check_error()
        return import_module('.imagesettings', package=__package__).ImageSettings._from_handle(result)

    def get_html_settings(self) -> 'HtmlSettings':
        """
        Gets the settings for HTML.

        Returns:
            'HtmlSettings': The HTML settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetHtmlSettings(self._handle)
        self._check_error()
        return import_module('.htmlsettings', package=__package__).HtmlSettings._from_handle(result)

    def get_document_layout_json_export_settings(self) -> 'DocumentLayoutJsonExportSettings':
        """
        Gets the settings for documentlayoutjsonexport.

        Returns:
            'DocumentLayoutJsonExportSettings': The documentlayoutjsonexport settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetDocumentLayoutJsonExportSettings(self._handle)
        self._check_error()
        return import_module('.documentlayoutjsonexportsettings', package=__package__).DocumentLayoutJsonExportSettings._from_handle(result)

    def get_words_detection_settings(self) -> 'WordsDetectionSettings':
        """
        Gets the settings for wordsdetection.

        Returns:
            'WordsDetectionSettings': The wordsdetection settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetWordsDetectionSettings(self._handle)
        self._check_error()
        return import_module('.wordsdetectionsettings', package=__package__).WordsDetectionSettings._from_handle(result)

    def get_vision_settings(self) -> 'VisionSettings':
        """
        Gets the settings for vision.

        Returns:
            'VisionSettings': The vision settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetVisionSettings(self._handle)
        self._check_error()
        return import_module('.visionsettings', package=__package__).VisionSettings._from_handle(result)

    def get_vision_descriptor_settings(self) -> 'VisionDescriptorSettings':
        """
        Gets the settings for visiondescriptor.

        Returns:
            'VisionDescriptorSettings': The visiondescriptor settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetVisionDescriptorSettings(self._handle)
        self._check_error()
        return import_module('.visiondescriptorsettings', package=__package__).VisionDescriptorSettings._from_handle(result)

    def get_table_recognition_settings(self) -> 'TableRecognitionSettings':
        """
        Gets the settings for tablerecognition.

        Returns:
            'TableRecognitionSettings': The tablerecognition settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetTableRecognitionSettings(self._handle)
        self._check_error()
        return import_module('.tablerecognitionsettings', package=__package__).TableRecognitionSettings._from_handle(result)

    def get_segmenter_settings(self) -> 'SegmenterSettings':
        """
        Gets the settings for segmenter.

        Returns:
            'SegmenterSettings': The segmenter settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetSegmenterSettings(self._handle)
        self._check_error()
        return import_module('.segmentersettings', package=__package__).SegmenterSettings._from_handle(result)

    def get_reading_order_settings(self) -> 'ReadingOrderSettings':
        """
        Gets the settings for readingorder.

        Returns:
            'ReadingOrderSettings': The readingorder settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetReadingOrderSettings(self._handle)
        self._check_error()
        return import_module('.readingordersettings', package=__package__).ReadingOrderSettings._from_handle(result)

    def get_open_ai_picture_alt_settings(self) -> 'OpenAIPictureAltSettings':
        """
        Gets the settings for openaipicturealt.

        Returns:
            'OpenAIPictureAltSettings': The openaipicturealt settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetOpenAIPictureAltSettings(self._handle)
        self._check_error()
        return import_module('.openaipicturealtsettings', package=__package__).OpenAIPictureAltSettings._from_handle(result)

    def get_open_ai_languages_detection_settings(self) -> 'OpenAILanguagesDetectionSettings':
        """
        Gets the settings for openailanguagesdetection.

        Returns:
            'OpenAILanguagesDetectionSettings': The openailanguagesdetection settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetOpenAILanguagesDetectionSettings(self._handle)
        self._check_error()
        return import_module('.openailanguagesdetectionsettings', package=__package__).OpenAILanguagesDetectionSettings._from_handle(result)

    def get_inference_layout_settings(self) -> 'InferenceLayoutSettings':
        """
        Gets the settings for inferencelayout.

        Returns:
            'InferenceLayoutSettings': The inferencelayout settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetInferenceLayoutSettings(self._handle)
        self._check_error()
        return import_module('.inferencelayoutsettings', package=__package__).InferenceLayoutSettings._from_handle(result)

    def get_finalizer_settings(self) -> 'FinalizerSettings':
        """
        Gets the settings for finalizer.

        Returns:
            'FinalizerSettings': The finalizer settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetFinalizerSettings(self._handle)
        self._check_error()
        return import_module('.finalizersettings', package=__package__).FinalizerSettings._from_handle(result)

    def get_content_extraction_settings(self) -> 'ContentExtractionSettings':
        """
        Gets the settings for contentextraction.

        Returns:
            'ContentExtractionSettings': The contentextraction settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetContentExtractionSettings(self._handle)
        self._check_error()
        return import_module('.contentextractionsettings', package=__package__).ContentExtractionSettings._from_handle(result)

    def get_open_ai_api_endpoint_settings(self) -> 'OpenAIApiEndpointSettings':
        """
        Gets the settings for openaiapiendpoint.

        Returns:
            'OpenAIApiEndpointSettings': The openaiapiendpoint settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetOpenAIApiEndpointSettings(self._handle)
        self._check_error()
        return import_module('.openaiapiendpointsettings', package=__package__).OpenAIApiEndpointSettings._from_handle(result)

    def get_custom_vlm_api_settings(self) -> 'CustomVlmApiSettings':
        """
        Gets the settings for customvlmapi.

        Returns:
            'CustomVlmApiSettings': The customvlmapi settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetCustomVlmApiSettings(self._handle)
        self._check_error()
        return import_module('.customvlmapisettings', package=__package__).CustomVlmApiSettings._from_handle(result)

    def get_claude_api_settings(self) -> 'ClaudeApiSettings':
        """
        Gets the settings for claudeapi.

        Returns:
            'ClaudeApiSettings': The claudeapi settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetClaudeApiSettings(self._handle)
        self._check_error()
        return import_module('.claudeapisettings', package=__package__).ClaudeApiSettings._from_handle(result)

    def get_ai_augmenter_settings(self) -> 'AiAugmenterSettings':
        """
        Gets the settings for aiaugmenter.

        Returns:
            'AiAugmenterSettings': The aiaugmenter settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetAiAugmenterSettings(self._handle)
        self._check_error()
        return import_module('.aiaugmentersettings', package=__package__).AiAugmenterSettings._from_handle(result)

    def get_conversion_settings(self) -> 'ConversionSettings':
        """
        Gets the settings for conversion.

        Returns:
            'ConversionSettings': The conversion settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetConversionSettings(self._handle)
        self._check_error()
        return import_module('.conversionsettings', package=__package__).ConversionSettings._from_handle(result)

    def get_cad_settings(self) -> 'CadSettings':
        """
        Gets the settings for CAD.

        Returns:
            'CadSettings': The CAD settings.

        Raises:
            DocumentSettingsError: If the operation fails
        """
        self._ensure_not_closed()

        result = _lib.BridgeDocumentSettingsGetCadSettings(self._handle)
        self._check_error()
        return import_module('.cadsettings', package=__package__).CadSettings._from_handle(result)

    @property
    def word_settings(self) -> 'WordSettings':
        """
        Gets the settings for Word documents.

        Returns:
            'WordSettings': The Word documents settings.
        """
        return self.get_word_settings()

    @property
    def tiff_settings(self) -> 'TiffSettings':
        """
        Gets the settings for tiff.

        Returns:
            'TiffSettings': The tiff settings.
        """
        return self.get_tiff_settings()

    @property
    def spreadsheet_settings(self) -> 'SpreadsheetSettings':
        """
        Gets the settings for spreadsheet.

        Returns:
            'SpreadsheetSettings': The spreadsheet settings.
        """
        return self.get_spreadsheet_settings()

    @property
    def presentation_settings(self) -> 'PresentationSettings':
        """
        Gets the settings for presentation.

        Returns:
            'PresentationSettings': The presentation settings.
        """
        return self.get_presentation_settings()

    @property
    def pdf_settings(self) -> 'PdfSettings':
        """
        Gets the settings for PDF.

        Returns:
            'PdfSettings': The PDF settings.
        """
        return self.get_pdf_settings()

    @property
    def pdf_page_settings(self) -> 'PdfPageSettings':
        """
        Gets the settings for PDF page.

        Returns:
            'PdfPageSettings': The PDF page settings.
        """
        return self.get_pdf_page_settings()

    @property
    def open_settings(self) -> 'OpenSettings':
        """
        Gets the settings for opening documents.

        Returns:
            'OpenSettings': The opening documents settings.
        """
        return self.get_open_settings()

    @property
    def ocr_settings(self) -> 'OcrSettings':
        """
        Gets the settings for ocr.

        Returns:
            'OcrSettings': The ocr settings.
        """
        return self.get_ocr_settings()

    @property
    def jpeg_settings(self) -> 'JpegSettings':
        """
        Gets the settings for jpeg.

        Returns:
            'JpegSettings': The jpeg settings.
        """
        return self.get_jpeg_settings()

    @property
    def jbig2_settings(self) -> 'Jbig2Settings':
        """
        Gets the settings for jbig2.

        Returns:
            'Jbig2Settings': The jbig2 settings.
        """
        return self.get_jbig2_settings()

    @property
    def image_settings(self) -> 'ImageSettings':
        """
        Gets the settings for image.

        Returns:
            'ImageSettings': The image settings.
        """
        return self.get_image_settings()

    @property
    def html_settings(self) -> 'HtmlSettings':
        """
        Gets the settings for HTML.

        Returns:
            'HtmlSettings': The HTML settings.
        """
        return self.get_html_settings()

    @property
    def document_layout_json_export_settings(self) -> 'DocumentLayoutJsonExportSettings':
        """
        Gets the settings for documentlayoutjsonexport.

        Returns:
            'DocumentLayoutJsonExportSettings': The documentlayoutjsonexport settings.
        """
        return self.get_document_layout_json_export_settings()

    @property
    def words_detection_settings(self) -> 'WordsDetectionSettings':
        """
        Gets the settings for wordsdetection.

        Returns:
            'WordsDetectionSettings': The wordsdetection settings.
        """
        return self.get_words_detection_settings()

    @property
    def vision_settings(self) -> 'VisionSettings':
        """
        Gets the settings for vision.

        Returns:
            'VisionSettings': The vision settings.
        """
        return self.get_vision_settings()

    @property
    def vision_descriptor_settings(self) -> 'VisionDescriptorSettings':
        """
        Gets the settings for visiondescriptor.

        Returns:
            'VisionDescriptorSettings': The visiondescriptor settings.
        """
        return self.get_vision_descriptor_settings()

    @property
    def table_recognition_settings(self) -> 'TableRecognitionSettings':
        """
        Gets the settings for tablerecognition.

        Returns:
            'TableRecognitionSettings': The tablerecognition settings.
        """
        return self.get_table_recognition_settings()

    @property
    def segmenter_settings(self) -> 'SegmenterSettings':
        """
        Gets the settings for segmenter.

        Returns:
            'SegmenterSettings': The segmenter settings.
        """
        return self.get_segmenter_settings()

    @property
    def reading_order_settings(self) -> 'ReadingOrderSettings':
        """
        Gets the settings for readingorder.

        Returns:
            'ReadingOrderSettings': The readingorder settings.
        """
        return self.get_reading_order_settings()

    @property
    def open_ai_picture_alt_settings(self) -> 'OpenAIPictureAltSettings':
        """
        Gets the settings for openaipicturealt.

        Returns:
            'OpenAIPictureAltSettings': The openaipicturealt settings.
        """
        return self.get_open_ai_picture_alt_settings()

    @property
    def open_ai_languages_detection_settings(self) -> 'OpenAILanguagesDetectionSettings':
        """
        Gets the settings for openailanguagesdetection.

        Returns:
            'OpenAILanguagesDetectionSettings': The openailanguagesdetection settings.
        """
        return self.get_open_ai_languages_detection_settings()

    @property
    def inference_layout_settings(self) -> 'InferenceLayoutSettings':
        """
        Gets the settings for inferencelayout.

        Returns:
            'InferenceLayoutSettings': The inferencelayout settings.
        """
        return self.get_inference_layout_settings()

    @property
    def finalizer_settings(self) -> 'FinalizerSettings':
        """
        Gets the settings for finalizer.

        Returns:
            'FinalizerSettings': The finalizer settings.
        """
        return self.get_finalizer_settings()

    @property
    def content_extraction_settings(self) -> 'ContentExtractionSettings':
        """
        Gets the settings for contentextraction.

        Returns:
            'ContentExtractionSettings': The contentextraction settings.
        """
        return self.get_content_extraction_settings()

    @property
    def open_ai_api_endpoint_settings(self) -> 'OpenAIApiEndpointSettings':
        """
        Gets the settings for openaiapiendpoint.

        Returns:
            'OpenAIApiEndpointSettings': The openaiapiendpoint settings.
        """
        return self.get_open_ai_api_endpoint_settings()

    @property
    def custom_vlm_api_settings(self) -> 'CustomVlmApiSettings':
        """
        Gets the settings for customvlmapi.

        Returns:
            'CustomVlmApiSettings': The customvlmapi settings.
        """
        return self.get_custom_vlm_api_settings()

    @property
    def claude_api_settings(self) -> 'ClaudeApiSettings':
        """
        Gets the settings for claudeapi.

        Returns:
            'ClaudeApiSettings': The claudeapi settings.
        """
        return self.get_claude_api_settings()

    @property
    def ai_augmenter_settings(self) -> 'AiAugmenterSettings':
        """
        Gets the settings for aiaugmenter.

        Returns:
            'AiAugmenterSettings': The aiaugmenter settings.
        """
        return self.get_ai_augmenter_settings()

    @property
    def conversion_settings(self) -> 'ConversionSettings':
        """
        Gets the settings for conversion.

        Returns:
            'ConversionSettings': The conversion settings.
        """
        return self.get_conversion_settings()

    @property
    def cad_settings(self) -> 'CadSettings':
        """
        Gets the settings for CAD.

        Returns:
            'CadSettings': The CAD settings.
        """
        return self.get_cad_settings()



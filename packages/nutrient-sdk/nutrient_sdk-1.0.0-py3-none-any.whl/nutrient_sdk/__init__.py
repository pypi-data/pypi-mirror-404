"""Nutrient SDK for Python."""

__version__ = "1.0.0"
__author__ = "Nutrient"
__license__ = "Commercial"

from .base_exception import (
    NutrientException,
    SDKError,
    InitializationError,
    LicenseError,
    DocumentError,
    ConversionError,
    ValidationError,
    IOError,
    MemoryError,
    TimeoutError,
    NotImplementedError,
    PermissionError,
    ErrorInfo,
    handle_native_error
)

from .iexporter import IExporter, IExporterBase


from .sdksettings import SdkSettings
from .license import License
from .internallogic import InternalLogic
from .document import Document
from .digitalsignatureoptions import DigitalSignatureOptions
from .pdfsigner import PdfSigner
from .signatureappearance import SignatureAppearance
from .timestampconfiguration import TimestampConfiguration
from .htmlexporter import HtmlExporter
from .imageexporter import ImageExporter
from .markdownexporter import MarkdownExporter
from .pdfexporter import PdfExporter
from .presentationexporter import PresentationExporter
from .spreadsheetexporter import SpreadsheetExporter
from .svgexporter import SvgExporter
from .wordexporter import WordExporter
from .pdfeditor import PdfEditor
from .wordeditor import WordEditor
from .pdfpage import PdfPage
from .pdfpagecollection import PdfPageCollection
from .pdfcheckboxfield import PdfCheckBoxField
from .pdfformfield import PdfFormField
from .pdfcomboboxfield import PdfComboBoxField
from .pdfformfieldcollection import PdfFormFieldCollection
from .pdflistboxfield import PdfListBoxField
from .pdfpushbuttonfield import PdfPushButtonField
from .pdfradiobuttonfield import PdfRadioButtonField
from .pdfsignaturefield import PdfSignatureField
from .pdftextfield import PdfTextField
from .pdfannotation import PdfAnnotation
from .pdfannotationcollection import PdfAnnotationCollection
from .pdflinkannotation import PdfLinkAnnotation
from .pdfmarkupannotation import PdfMarkupAnnotation
from .pdffreetextannotation import PdfFreeTextAnnotation
from .pdfwidgetannotation import PdfWidgetAnnotation
from .pdfstampannotation import PdfStampAnnotation
from .pdfredactannotation import PdfRedactAnnotation
from .pdfshapeannotation import PdfShapeAnnotation
from .pdflineannotation import PdfLineAnnotation
from .pdfcircleannotation import PdfCircleAnnotation
from .pdfsquareannotation import PdfSquareAnnotation
from .pdftextannotation import PdfTextAnnotation
from .pdfhighlightannotation import PdfHighlightAnnotation
from .pdfunderlineannotation import PdfUnderlineAnnotation
from .pdfstrikeoutannotation import PdfStrikeOutAnnotation
from .pdfsquigglyannotation import PdfSquigglyAnnotation
from .vision import Vision
from .color import Color
from .aiaugmentersettings import AiAugmenterSettings
from .cadsettings import CadSettings
from .documentsettings import DocumentSettings
from .claudeapisettings import ClaudeApiSettings
from .pdfmetadata import PdfMetadata
from .contentextractionsettings import ContentExtractionSettings
from .documentlayoutjsonexportsettings import DocumentLayoutJsonExportSettings
from .conversionsettings import ConversionSettings
from .customvlmapisettings import CustomVlmApiSettings
from .finalizersettings import FinalizerSettings
from .htmlsettings import HtmlSettings
from .imagesettings import ImageSettings
from .inferencelayoutsettings import InferenceLayoutSettings
from .jbig2settings import Jbig2Settings
from .jpegsettings import JpegSettings
from .ocrsettings import OcrSettings
from .openaiapiendpointsettings import OpenAIApiEndpointSettings
from .openailanguagesdetectionsettings import OpenAILanguagesDetectionSettings
from .openaipicturealtsettings import OpenAIPictureAltSettings
from .opensettings import OpenSettings
from .pdfpagesettings import PdfPageSettings
from .pdfsettings import PdfSettings
from .presentationsettings import PresentationSettings
from .readingordersettings import ReadingOrderSettings
from .segmentersettings import SegmenterSettings
from .spreadsheetsettings import SpreadsheetSettings
from .tablerecognitionsettings import TableRecognitionSettings
from .tiffsettings import TiffSettings
from .visiondescriptorsettings import VisionDescriptorSettings
from .visionsettings import VisionSettings
from .wordsdetectionsettings import WordsDetectionSettings
from .wordsettings import WordSettings

from .pdfpagesizes import PdfPageSizes
from .renderinglayoutmode import RenderingLayoutMode
from .pdfformfieldtype import PdfFormFieldType
from .unitmode import UnitMode
from .documenttype import DocumentType
from .signaturehashalgorithm import SignatureHashAlgorithm
from .jsonexportcontent import JsonExportContent
from .jsonexportformat import JsonExportFormat
from .tiffcompression import TiffCompression
from .descriptionlevel import DescriptionLevel
from .pdfborderstyle import PdfBorderStyle
from .vlmprovider import VlmProvider
from .visionfeatures import VisionFeatures
from .visionengine import VisionEngine
from .documentmarkupmode import DocumentMarkupMode
from .textdirection import TextDirection
from .pdfrubberstampicon import PdfRubberStampIcon
from .pagecachemode import PageCacheMode
from .opensettingsmode import OpenSettingsMode
from .documentformat import DocumentFormat
from .implicitconversion import ImplicitConversion
from .pdfconformance import PdfConformance
from .pdfsettingsmode import PdfSettingsMode
from .pdfsavepreferences import PdfSavePreferences
from .pdfcompression import PdfCompression
from .pdflineendingstyle import PdfLineEndingStyle
from .htmllayouttype import HtmlLayoutType
from .imagesettingmode import ImageSettingMode
from .imageexportformat import ImageExportFormat

from .sdk_loader import (
    initialize_sdk,
    shutdown_sdk,
    get_sdk_version,
    is_sdk_initialized,
    SDKError
)

__all__ = [
    'initialize_sdk',
    'shutdown_sdk',
    'get_sdk_version',
    'is_sdk_initialized',
    'NutrientException',
    'SDKError',
    'InitializationError',
    'LicenseError',
    'DocumentError',
    'ConversionError',
    'ValidationError',
    'IOError',
    'MemoryError',
    'TimeoutError',
    'NotImplementedError',
    'PermissionError',
    'ErrorInfo',
    'handle_native_error',
    'IExporter',
    'IExporterBase',
    'SdkSettings',
    'License',
    'InternalLogic',
    'Document',
    'DigitalSignatureOptions',
    'PdfSigner',
    'SignatureAppearance',
    'TimestampConfiguration',
    'HtmlExporter',
    'ImageExporter',
    'MarkdownExporter',
    'PdfExporter',
    'PresentationExporter',
    'SpreadsheetExporter',
    'SvgExporter',
    'WordExporter',
    'PdfEditor',
    'WordEditor',
    'PdfPage',
    'PdfPageCollection',
    'PdfCheckBoxField',
    'PdfFormField',
    'PdfComboBoxField',
    'PdfFormFieldCollection',
    'PdfListBoxField',
    'PdfPushButtonField',
    'PdfRadioButtonField',
    'PdfSignatureField',
    'PdfTextField',
    'PdfAnnotation',
    'PdfAnnotationCollection',
    'PdfLinkAnnotation',
    'PdfMarkupAnnotation',
    'PdfFreeTextAnnotation',
    'PdfWidgetAnnotation',
    'PdfStampAnnotation',
    'PdfRedactAnnotation',
    'PdfShapeAnnotation',
    'PdfLineAnnotation',
    'PdfCircleAnnotation',
    'PdfSquareAnnotation',
    'PdfTextAnnotation',
    'PdfHighlightAnnotation',
    'PdfUnderlineAnnotation',
    'PdfStrikeOutAnnotation',
    'PdfSquigglyAnnotation',
    'Vision',
    'Color',
    'AiAugmenterSettings',
    'CadSettings',
    'DocumentSettings',
    'ClaudeApiSettings',
    'PdfMetadata',
    'ContentExtractionSettings',
    'DocumentLayoutJsonExportSettings',
    'ConversionSettings',
    'CustomVlmApiSettings',
    'FinalizerSettings',
    'HtmlSettings',
    'ImageSettings',
    'InferenceLayoutSettings',
    'Jbig2Settings',
    'JpegSettings',
    'OcrSettings',
    'OpenAIApiEndpointSettings',
    'OpenAILanguagesDetectionSettings',
    'OpenAIPictureAltSettings',
    'OpenSettings',
    'PdfPageSettings',
    'PdfSettings',
    'PresentationSettings',
    'ReadingOrderSettings',
    'SegmenterSettings',
    'SpreadsheetSettings',
    'TableRecognitionSettings',
    'TiffSettings',
    'VisionDescriptorSettings',
    'VisionSettings',
    'WordsDetectionSettings',
    'WordSettings',
    'PdfPageSizes',
    'RenderingLayoutMode',
    'PdfFormFieldType',
    'UnitMode',
    'DocumentType',
    'SignatureHashAlgorithm',
    'JsonExportContent',
    'JsonExportFormat',
    'TiffCompression',
    'DescriptionLevel',
    'PdfBorderStyle',
    'VlmProvider',
    'VisionFeatures',
    'VisionEngine',
    'DocumentMarkupMode',
    'TextDirection',
    'PdfRubberStampIcon',
    'PageCacheMode',
    'OpenSettingsMode',
    'DocumentFormat',
    'ImplicitConversion',
    'PdfConformance',
    'PdfSettingsMode',
    'PdfSavePreferences',
    'PdfCompression',
    'PdfLineEndingStyle',
    'HtmlLayoutType',
    'ImageSettingMode',
    'ImageExportFormat',
]

_initialized = False

def _auto_initialize():
    global _initialized
    if not _initialized:
        try:
            initialize_sdk()
            _initialized = True
        except SDKError as e:
            import warnings
            warnings.warn(f"Failed to auto-initialize Nutrient SDK: {e}", RuntimeWarning)

import os
if not os.environ.get('NUTRIENT_NO_AUTO_INIT'):
    _auto_initialize()

import atexit

def _cleanup():
    global _initialized
    if _initialized:
        try:
            shutdown_sdk()
            _initialized = False
        except:
            pass  # Ignore errors during cleanup

atexit.register(_cleanup)
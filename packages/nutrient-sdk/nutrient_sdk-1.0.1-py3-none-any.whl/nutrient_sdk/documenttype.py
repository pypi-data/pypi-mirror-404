"""
The type of the document currently used.
"""

from enum import Enum, auto
import ctypes

class DocumentType(Enum):
    """The type of the document currently used.."""
    
    DOCUMENT_TYPE_UNKNOWN = 0
    # Unknown or undefined document type.
    
    DOCUMENT_TYPE_BITMAP = 1
    # Raster image.
    
    DOCUMENT_TYPE_META_FILE = 2
    # Metafile image.
    
    DOCUMENT_TYPE_PDF = 3
    # PDF.
    
    DOCUMENT_TYPE_SVG = 4
    # SVG.
    
    DOCUMENT_TYPE_TXT = 5
    # Text-based document.
    
    DOCUMENT_TYPE_OPEN_XMLWORD = 6
    # Open XML Wordprocessing.
    
    DOCUMENT_TYPE_RTF = 7
    # RTF format.
    
    DOCUMENT_TYPE_DXF = 8
    # DXF format.
    
    DOCUMENT_TYPE_OPEN_DOCUMENT_TEXT = 9
    # OpenDocument Text format.
    
    DOCUMENT_TYPE_OPEN_XMLSPREADSHEET = 10
    # Open XML Spreadsheet.
    
    DOCUMENT_TYPE_OPEN_XMLPRESENTATION = 11
    # Open XML Presentation.
    
    DOCUMENT_TYPE_WORD_BINARY = 12
    # Word (.doc) Binary File Format.
    
    DOCUMENT_TYPE_EXCEL_BINARY = 13
    # Excel (.xls) Binary File Format.
    
    DOCUMENT_TYPE_POWER_POINT_BINARY = 14
    # PowerPoint (.ppt) Binary File Format.
    
    DOCUMENT_TYPE_HTML = 15
    # HTML Format.
    
    DOCUMENT_TYPE_MSG = 16
    # Outlook Message Item File format.
    
    DOCUMENT_TYPE_EML = 17
    # E-Mail Message format.
    
    DOCUMENT_TYPE_POST_SCRIPT = 18
    # PostScript format.
    
    DOCUMENT_TYPE_DWG = 19
    # Binary CAD format
    
    DOCUMENT_TYPE_MHTML = 20
    
    DOCUMENT_TYPE_MD = 21
    # Markdown text file format.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'DocumentType':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding DocumentType instance
            
        Raises:
            ValueError: If the value doesn't correspond to a valid enum member
        """
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Invalid {cls.__name__} value: {value}")
    
    def to_ctype(self) -> ctypes.c_int:
        """
        Convert to ctypes representation for native calls.
        
        Returns:
            ctypes.c_int: The enum value as a ctypes integer
        """
        return ctypes.c_int(self.value)
    
    def __str__(self) -> str:
        """String representation of the enum value."""
        return f"{self.__class__.__name__}.{self.name}"
    
    def __repr__(self) -> str:
        """Detailed representation of the enum value."""
        return f"<{self.__class__.__name__}.{self.name}: {self.value}>"

__all__ = ['DocumentType']


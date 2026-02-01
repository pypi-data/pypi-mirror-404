"""
Defines the format of the currently processed/used document.
"""

from enum import Enum, auto
import ctypes

class DocumentFormat(Enum):
    """Defines the format of the currently processed/used document.."""
    
    DOCUMENT_FORMAT_UNKNOWN = 0
    # Unknown or undefined document format. It is also returned if any error occurs.
    
    DOCUMENT_FORMAT_ICO = 1
    # Icon and cursor format (single or multi page).
    
    DOCUMENT_FORMAT_BMP = 2
    # Standard Windows Bitmap Format.
    
    DOCUMENT_FORMAT_WBMP = 3
    # Wireless Bitmap.
    
    DOCUMENT_FORMAT_JPEG = 4
    # Joint Photographic Expert Group.
    
    DOCUMENT_FORMAT_GIF = 5
    # Graphics Interchange Format.
    
    DOCUMENT_FORMAT_PNG = 6
    # Portable Network Graphics Format.
    
    DOCUMENT_FORMAT_TIFF = 7
    # Tagged Image Format.
    
    DOCUMENT_FORMAT_FAXG3 = 8
    # Group 3 Raw Fax Format.
    
    DOCUMENT_FORMAT_EXIF = 9
    # Exchangeable Image Format.
    
    DOCUMENT_FORMAT_EMF = 10
    # Enhanced Windows Meta-format.
    
    DOCUMENT_FORMAT_WMF = 11
    # Standard Windows Meta-format.
    
    DOCUMENT_FORMAT_JNG = 12
    # JPEG Network Graphics.
    
    DOCUMENT_FORMAT_KOALA = 13
    # KOALA Format.
    
    DOCUMENT_FORMAT_IFF = 14
    # Interchange Format.
    
    DOCUMENT_FORMAT_MNG = 15
    # Multiple-image Network Graphics.
    
    DOCUMENT_FORMAT_PCD = 16
    # Kodak Photo-CD file.
    
    DOCUMENT_FORMAT_PCX = 17
    # PC Paintbrush Format.
    
    DOCUMENT_FORMAT_PBM = 18
    # Portable Bitmap File.
    
    DOCUMENT_FORMAT_PBMRAW = 19
    # Portable Bitmap BINARY.
    
    DOCUMENT_FORMAT_PFM = 20
    # Portable Float Map.
    
    DOCUMENT_FORMAT_PGM = 21
    # Portable Gray-map File.
    
    DOCUMENT_FORMAT_PGMRAW = 22
    # Portable Gray-map BINARY.
    
    DOCUMENT_FORMAT_PPM = 23
    # Portable Pix-map File.
    
    DOCUMENT_FORMAT_PPMRAW = 24
    # Portable Pix-map BINARY.
    
    DOCUMENT_FORMAT_RAS = 25
    # Sun Raster Format.
    
    DOCUMENT_FORMAT_TARGA = 26
    # TARGA Image Format.
    
    DOCUMENT_FORMAT_PSD = 27
    # Photoshop File.
    
    DOCUMENT_FORMAT_CUT = 28
    # Dr. Halo/Dr.Genius Clipboard Format.
    
    DOCUMENT_FORMAT_XBM = 29
    # X-Bitmap Format.
    
    DOCUMENT_FORMAT_XPM = 30
    # X Pixmap Format.
    
    DOCUMENT_FORMAT_DDS = 31
    # Microsoft Direct-draw Surface Format.
    
    DOCUMENT_FORMAT_HDR = 32
    # High Dynamic Range Format.
    
    DOCUMENT_FORMAT_SGI = 33
    # Silicon Graphics Image Format.
    
    DOCUMENT_FORMAT_EXR = 34
    # OpenEXR Format.
    
    DOCUMENT_FORMAT_J2_K = 35
    # JPEG-2000 Code-stream.
    
    DOCUMENT_FORMAT_JP2 = 36
    # JPEG-2000 Format.
    
    DOCUMENT_FORMAT_JBIG = 37
    # Joint Bi-level Image Experts Group.
    
    DOCUMENT_FORMAT_PICT = 38
    # Macintosh PICT Format
    
    DOCUMENT_FORMAT_RAW = 39
    # RAW bitmap.
    
    DOCUMENT_FORMAT_WEBP = 40
    # WebP format.
    
    DOCUMENT_FORMAT_DICOM = 41
    # Digital Imaging and Communications in Medicine.
    
    DOCUMENT_FORMAT_WSQ = 42
    # Wavelet scalar quantization.
    
    DOCUMENT_FORMAT_HEIF = 43
    # High Efficiency Image File Format.
    
    DOCUMENT_FORMAT_JBIG2 = 100
    # Joint Bi-level Image Experts Group.
    
    DOCUMENT_FORMAT_MEMORY_BMP = 500
    # Standard Windows Bitmap Format using memory.
    
    DOCUMENT_FORMAT_PDF = 1000
    # Portable Document Format.
    
    DOCUMENT_FORMAT_SVG = 1001
    # Scalable Vector Graphics.
    
    DOCUMENT_FORMAT_TXT = 1002
    # Plain text file.
    
    DOCUMENT_FORMAT_DOCX = 1003
    # Microsoft Word OpenXML.
    
    DOCUMENT_FORMAT_RTF = 1004
    # Rich Text File Format.
    
    DOCUMENT_FORMAT_DXF = 1005
    # AutoCAD DXF (Drawing Interchange Format, or Drawing Exchange Format).
    
    DOCUMENT_FORMAT_ODT = 1006
    # OpenDocument text file format.
    
    DOCUMENT_FORMAT_XLSX = 1007
    # Microsoft Excel Spreadsheet format.
    
    DOCUMENT_FORMAT_PPTX = 1008
    # Microsoft Powerpoint Presentation format.
    
    DOCUMENT_FORMAT_DOC = 1009
    # Microsoft Word (.doc) binary file format.
    
    DOCUMENT_FORMAT_XLS = 1010
    # Microsoft Excel (.xls) binary file format.
    
    DOCUMENT_FORMAT_PPT = 1011
    # Microsoft PowerPoint (.ppt) binary file format.
    
    DOCUMENT_FORMAT_HTML = 1012
    # HTML format.
    
    DOCUMENT_FORMAT_MSG = 1013
    # Outlook Message Item File format.
    
    DOCUMENT_FORMAT_EML = 1014
    # E-Mail Message format.
    
    DOCUMENT_FORMAT_POST_SCRIPT = 1015
    # PostScript format.
    
    DOCUMENT_FORMAT_DWG = 1016
    # Binary CAD format
    
    DOCUMENT_FORMAT_MHTML = 1017
    # MIME HTML format.
    
    DOCUMENT_FORMAT_MD = 1018
    # Markdown text file format.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'DocumentFormat':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding DocumentFormat instance
            
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

__all__ = ['DocumentFormat']


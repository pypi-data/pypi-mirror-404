"""
Specifies the standard scheme to be used to compress image data in PDF documents.
"""

from enum import Enum, auto
import ctypes

class PdfCompression(Enum):
    """Specifies the standard scheme to be used to compress image data in PDF documents.."""
    
    PDF_COMPRESSION_NONE = 0
    # No compression.
    
    PDF_COMPRESSION_FLATE = 1
    # Zlib/deflate compression method.
    
    PDF_COMPRESSION_CCITT4 = 2
    # CCITT 4 facsimile standard.
    
    PDF_COMPRESSION_JPEG = 3
    # DCT (discrete cosine transform) technique based on the JPEG standard.
    
    PDF_COMPRESSION_JBIG2 = 4
    # JBIG2 standard.
    
    PDF_COMPRESSION_JPEG2000 = 5
    # Wavelet-based JPEG2000 standard.
    
    PDF_COMPRESSION_UNKNOWN = -1
    # Unknown compression.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'PdfCompression':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding PdfCompression instance
            
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

__all__ = ['PdfCompression']


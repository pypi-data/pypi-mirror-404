"""
Specifies the TIFF compression when saving images in TIFF format.
"""

from enum import Enum, auto
import ctypes

class TiffCompression(Enum):
    """Specifies the TIFF compression when saving images in TIFF format.."""
    
    TIFF_COMPRESSION_UNKNOWN = 0
    # Unknown compression.
    
    TIFF_COMPRESSION_NONE = 1
    # No compression.
    
    TIFF_COMPRESSION_RLE = 2
    # CCITT modified Huffman RLE
    
    TIFF_COMPRESSION_CCITT3 = 3
    # CCITT Group 3 fax encoding
    
    TIFF_COMPRESSION_CCITT4 = 4
    # CCITT Group 4 fax encoding
    
    TIFF_COMPRESSION_LZW = 5
    # Lempel-Ziv and Welch
    
    TIFF_COMPRESSION_OJPEG = 6
    # !6.0 JPEG
    
    TIFF_COMPRESSION_JPEG = 7
    # %JPEG DCT compression
    
    TIFF_COMPRESSION_ADOBEDEFLATE = 8
    # Deflate compression, as recognized by Adobe.
    
    TIFF_COMPRESSION_NEXT = 32766
    # NeXT 2-bit RLE
    
    TIFF_COMPRESSION_CCITTRLEW = 32771
    # #1 w/ word alignment
    
    TIFF_COMPRESSION_PACKBITS = 32773
    # Macintosh RLE
    
    TIFF_COMPRESSION_THUNDERSCAN = 32809
    # ThunderScan RLE
    
    TIFF_COMPRESSION_DEFLATE = 32946
    # Deflate compression.
    
    TIFF_COMPRESSION_AUTO = 65536
    # Uses CCITT4 compression for bitonal image and LZW for others. TiffCompressionAUTO allows to mix compression in a multipage tiff document.
    
    TIFF_COMPRESSION_AUTO2 = 65537
    # Beta: do not use yet.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'TiffCompression':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding TiffCompression instance
            
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

__all__ = ['TiffCompression']


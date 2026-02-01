"""
Specifies PDF versions and conformance levels of a PDF document. The PDF versions correspond to the PDF major releases, starting from PDF 1.0. In each PDF version the new features have been introduced. The different conformance levels reflect the quality of the archived document and depend on the input material and the documents purpose. PDF/A versions and levels are given one after another.PDF/A-1 is the first archiving standard based on PDF version 1.4. All resources must be embedded within the PDF/A document itself.PDF/A-2 is based on PDF 1.7. It allows JPEG2000 compression, transparent elements, PDF layers and more.PDF/A-3 is available since October 2012. It allows to embed any file format desired.Level a (accessible) meets all requirements for the standard.Level b (basic) guaranteed that the content of the document can be unambiguously reproduced.Level u (unicode) specifies that all text can be mapped to standard Unicode character codes.
"""

from enum import Enum, auto
import ctypes

class PdfConformance(Enum):
    """Specifies PDF versions and conformance levels of a PDF document. The PDF versions correspond to the PDF major releases, starting from PDF 1.0. In each PDF version the new features have been introduced. The different conformance levels reflect the quality of the archived document and depend on the input material and the documents purpose. PDF/A versions and levels are given one after another.PDF/A-1 is the first archiving standard based on PDF version 1.4. All resources must be embedded within the PDF/A document itself.PDF/A-2 is based on PDF 1.7. It allows JPEG2000 compression, transparent elements, PDF layers and more.PDF/A-3 is available since October 2012. It allows to embed any file format desired.Level a (accessible) meets all requirements for the standard.Level b (basic) guaranteed that the content of the document can be unambiguously reproduced.Level u (unicode) specifies that all text can be mapped to standard Unicode character codes.."""
    
    PDF = 0
    # This is a common PDF document. Read more about PDF compatibility levels here .
    
    PDF_A_1A = 1
    # The PDF conformance level is PDF/A-1a.
    
    PDF_A_1B = 2
    # The PDF conformance level is PDF/A-1b.
    
    PDF_A_2A = 3
    # The PDF conformance level is PDF/A-2a.
    
    PDF_A_2U = 4
    # The PDF conformance level is PDF/A-2u.
    
    PDF_A_2B = 5
    # The PDF conformance level is PDF/A-2b.
    
    PDF_A_3A = 6
    # The PDF conformance level is PDF/A-3a.
    
    PDF_A_3U = 7
    # The PDF conformance level is PDF/A-3u.
    
    PDF_A_3B = 8
    # The PDF conformance level is PDF/A-3b.
    
    PDF_A_4 = 9
    # The PDF conformance level is PDF/A-4.
    
    PDF_A_4E = 10
    # The PDF conformance level is PDF/A-4e.
    
    PDF_A_4F = 11
    # The PDF conformance level is PDF/A-4f.
    
    PDF1_0 = 12
    # The PDF version is PDF 1.0.
    
    PDF1_1 = 13
    # The PDF version is PDF 1.1.
    
    PDF1_2 = 14
    # The PDF version is PDF 1.2.
    
    PDF1_3 = 15
    # The PDF version is PDF 1.3.
    
    PDF1_4 = 16
    # The PDF version is PDF 1.4.
    
    PDF1_5 = 17
    # The PDF version is PDF 1.5.
    
    PDF1_6 = 18
    # The PDF version is PDF 1.6.
    
    PDF1_7 = 19
    # The PDF version is PDF 1.7.
    
    PDF2_0 = 20
    # The PDF version is PDF 2.0 (ISO 32000-2).
    
    PDF_UA_1 = 21
    # The PDF conformance level is PDF/UA-1.
    
    UNKNOWN = -1
    # The PDF conformance level is unknown.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'PdfConformance':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding PdfConformance instance
            
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

__all__ = ['PdfConformance']


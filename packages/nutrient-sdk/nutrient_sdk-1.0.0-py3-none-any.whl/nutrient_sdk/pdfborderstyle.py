"""
Specifies the border style for annotations.
"""

from enum import Enum, auto
import ctypes

class PdfBorderStyle(Enum):
    """Specifies the border style for annotations.."""
    
    SOLID = 0
    # A solid rectangle surrounding the annotation.
    
    DASHED = 1
    # A dashed rectangle surrounding the annotation.
    
    BEVELED = 2
    # A simulated embossed rectangle that appears raised above the page surface.
    
    INSET = 3
    # A simulated engraved rectangle that appears recessed below the page surface.
    
    UNDERLINE = 4
    # A single line along the bottom of the annotation rectangle.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'PdfBorderStyle':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding PdfBorderStyle instance
            
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

__all__ = ['PdfBorderStyle']


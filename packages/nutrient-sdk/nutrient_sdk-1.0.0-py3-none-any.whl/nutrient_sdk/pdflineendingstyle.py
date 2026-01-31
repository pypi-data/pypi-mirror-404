"""
Specifies the style of line endings for line annotations.
"""

from enum import Enum, auto
import ctypes

class PdfLineEndingStyle(Enum):
    """Specifies the style of line endings for line annotations.."""
    
    NONE = 0
    # No line ending.
    
    SQUARE = 1
    # A square filled with the annotation's interior color.
    
    CIRCLE = 2
    # A circle filled with the annotation's interior color.
    
    DIAMOND = 3
    # A diamond shape filled with the annotation's interior color.
    
    OPEN_ARROW = 4
    # Two short lines meeting in an acute angle to form an open arrowhead.
    
    CLOSED_ARROW = 5
    # A triangular closed arrowhead filled with the annotation's interior color.
    
    BUTT = 6
    # A short line at the endpoint perpendicular to the line itself.
    
    REVERSE_OPEN_ARROW = 7
    # Two short lines in the reverse direction from OpenArrow.
    
    REVERSE_CLOSED_ARROW = 8
    # A triangular closed arrowhead in the reverse direction from ClosedArrow.
    
    SLASH = 9
    # A short line at the endpoint approximately 30 degrees clockwise from perpendicular.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'PdfLineEndingStyle':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding PdfLineEndingStyle instance
            
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

__all__ = ['PdfLineEndingStyle']


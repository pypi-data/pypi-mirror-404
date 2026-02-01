"""
Specifies the modes for converting document markups, including how changes and comments are rendered.
"""

from enum import Enum, auto
import ctypes

class DocumentMarkupMode(Enum):
    """Specifies the modes for converting document markups, including how changes and comments are rendered.."""
    
    ALL_MARKUP = 0
    # Show all the markups in different colors, underlined/struck through. Comments are converted to annotations. This is the default behavior.
    
    SIMPLE_MARKUP = 1
    # Show the document as if all the changes were accepted. Comments are converted to annotations.
    
    NO_MARKUP = 2
    # Show the document as if all the changes were accepted. Comments are NOT converted to annotations.
    
    ORIGINAL = 3
    # Show the document as if none of the changes were made (= as if all changes were rejected) Comments are NOT converted to annotations.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'DocumentMarkupMode':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding DocumentMarkupMode instance
            
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

__all__ = ['DocumentMarkupMode']


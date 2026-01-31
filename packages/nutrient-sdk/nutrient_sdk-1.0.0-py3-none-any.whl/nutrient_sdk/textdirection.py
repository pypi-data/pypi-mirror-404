"""
Text direction modes for reading order computation.
"""

from enum import Enum, auto
import ctypes

class TextDirection(Enum):
    """Text direction modes for reading order computation.."""
    
    LEFT_TO_RIGHT_TOP_TO_BOTTOM = 0
    # Left-to-right, then top-to-bottom (e.g., English, most European languages)
    
    RIGHT_TO_LEFT_TOP_TO_BOTTOM = 1
    # Right-to-left, then top-to-bottom (e.g., Arabic, Hebrew)
    
    TOP_TO_BOTTOM_RIGHT_TO_LEFT = 2
    # Top-to-bottom, then right-to-left (e.g., Traditional Chinese, Japanese vertical)
    
    TOP_TO_BOTTOM_LEFT_TO_RIGHT = 3
    # Top-to-bottom, then left-to-right (e.g., Mongolian vertical)
    
    
    @classmethod
    def from_value(cls, value: int) -> 'TextDirection':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding TextDirection instance
            
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

__all__ = ['TextDirection']


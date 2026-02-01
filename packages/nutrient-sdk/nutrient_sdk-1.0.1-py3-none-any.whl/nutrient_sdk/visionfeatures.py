"""
Vision processing features that can be enabled or disabled.
"""

from enum import Enum, auto
import ctypes

class VisionFeatures(Enum):
    """Vision processing features that can be enabled or disabled.."""
    
    UNKNOWN = 0
    # No features enabled.
    
    EQUATION = 1
    # Mathematical equation detection and recognition.
    
    TABLE = 2
    # Table structure detection and extraction.
    
    KEY_VALUE_REGION = 4
    # Key-value region detection for form-like content.
    
    IMAGE_CLASSIFICATION = 8
    # Image classification for figures and diagrams.
    
    HANDWRITTING = 16
    # Image classification for figures and diagrams.
    
    ALL = 31
    # All vision features enabled.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'VisionFeatures':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding VisionFeatures instance
            
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

__all__ = ['VisionFeatures']


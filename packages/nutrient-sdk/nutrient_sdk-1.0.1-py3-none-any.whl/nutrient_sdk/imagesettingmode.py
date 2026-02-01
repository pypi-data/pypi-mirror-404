"""
Specifies the mode options for image settings.
"""

from enum import Enum, auto
import ctypes

class ImageSettingMode(Enum):
    """Specifies the mode options for image settings.."""
    
    UNSPECIFIED = 0
    # No specific mode is set.
    
    FOLLOW_EXIF_ROTATION = 1
    # Specifies if the Exif Rotation information should be followed if it's present in the loaded document
    
    PRESERVE_ICC_PROFILE = 2
    # Specifies if the ICC profile should be preserved during the conversion if it's present in the loaded document.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'ImageSettingMode':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding ImageSettingMode instance
            
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

__all__ = ['ImageSettingMode']


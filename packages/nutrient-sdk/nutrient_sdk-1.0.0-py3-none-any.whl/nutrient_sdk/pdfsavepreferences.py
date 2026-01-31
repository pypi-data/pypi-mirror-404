"""
Specifies preferences for saving PDF documents.
"""

from enum import Enum, auto
import ctypes

class PdfSavePreferences(Enum):
    """Specifies preferences for saving PDF documents.."""
    
    NONE = 0
    # No specific preferences are set.
    
    APPLY_REDACTIONS = 1
    # Automatically apply redaction annotations when saving PDF documents. When enabled, all redaction annotations are applied (content is permanently removed) during save operations. The redaction annotations are removed after applying.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'PdfSavePreferences':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding PdfSavePreferences instance
            
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

__all__ = ['PdfSavePreferences']


"""
Specifies formatting options for JSON export.
"""

from enum import Enum, auto
import ctypes

class JsonExportFormat(Enum):
    """Specifies formatting options for JSON export.."""
    
    UNSPECIFIED = 0
    # No specific formatting options.
    
    PRETTY_PRINT = 1
    # Format the JSON output with indentation for readability.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'JsonExportFormat':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding JsonExportFormat instance
            
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

__all__ = ['JsonExportFormat']


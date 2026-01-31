"""
Description detail levels for Vision document description.
"""

from enum import Enum, auto
import ctypes

class DescriptionLevel(Enum):
    """Description detail levels for Vision document description.."""
    
    UNKNOWN = 0
    # No description.
    
    STANDARD = 1
    # Standard concise description.
    
    DETAILED = 2
    # Detailed description with additional context.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'DescriptionLevel':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding DescriptionLevel instance
            
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

__all__ = ['DescriptionLevel']


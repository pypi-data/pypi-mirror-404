"""
Specifies different unit modes.
"""

from enum import Enum, auto
import ctypes

class UnitMode(Enum):
    """Specifies different unit modes.."""
    
    UNIT_WORLD = 0
    # Do not use.
    
    UNIT_DISPLAY = 1
    # Do not use.
    
    UNIT_PIXEL = 2
    # Each unit is one device pixel.
    
    UNIT_POINT = 3
    # Each unit is a printer's point, or 1/72 inch.
    
    UNIT_INCH = 4
    # Each unit is 1 inch.
    
    UNIT_DOCUMENT = 5
    # Each unit is 1/300 inch.
    
    UNIT_MILLIMETER = 6
    # Each unit is 1 millimeter.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'UnitMode':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding UnitMode instance
            
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

__all__ = ['UnitMode']


"""
Defines the cache mode for the page.
"""

from enum import Enum, auto
import ctypes

class PageCacheMode(Enum):
    """Defines the cache mode for the page.."""
    
    MEMORY = 0
    # Page content is cached in an allocated memory buffer.
    
    FILE = 1
    # Page content is cached in a temporary file.
    
    FILE_NO_DELETE_ON_CLOSE = 2
    # Page content is cached in a temporary file that is not deleted on closing.
    
    UNSPECIFIED = -1
    # Here for internal usage. Do not use.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'PageCacheMode':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding PageCacheMode instance
            
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

__all__ = ['PageCacheMode']


"""
Specifies the hash algorithm to use when creating a digital signature.
"""

from enum import Enum, auto
import ctypes

class SignatureHashAlgorithm(Enum):
    """Specifies the hash algorithm to use when creating a digital signature.."""
    
    SHA256 = 1
    # SHA-256 hash algorithm. This is the recommended default.
    
    SHA512 = 2
    # SHA-512 hash algorithm.
    
    SHA384 = 4
    # SHA-384 hash algorithm.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'SignatureHashAlgorithm':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding SignatureHashAlgorithm instance
            
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

__all__ = ['SignatureHashAlgorithm']


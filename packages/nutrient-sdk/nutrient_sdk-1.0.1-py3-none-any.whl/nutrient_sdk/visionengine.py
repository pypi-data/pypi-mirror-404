"""
Specifies which vision processing pipeline to use for content extraction.
"""

from enum import Enum, auto
import ctypes

class VisionEngine(Enum):
    """Specifies which vision processing pipeline to use for content extraction.."""
    
    VLM_ENHANCED_ICR = 0
    # VLM-enhanced ICR extraction pipeline combining ICR with Vision Language Models.
    
    OCR = 1
    # Fast OCR-only extraction pipeline.
    
    ICR = 2
    # Local ICR extraction pipeline using only ONNX models (no VLM required).
    
    
    @classmethod
    def from_value(cls, value: int) -> 'VisionEngine':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding VisionEngine instance
            
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

__all__ = ['VisionEngine']


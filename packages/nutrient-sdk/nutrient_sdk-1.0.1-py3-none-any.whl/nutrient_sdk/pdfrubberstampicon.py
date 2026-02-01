"""
Specifies the predefined icon for a rubber stamp annotation.
"""

from enum import Enum, auto
import ctypes

class PdfRubberStampIcon(Enum):
    """Specifies the predefined icon for a rubber stamp annotation.."""
    
    APPROVED = 0
    # An "Approved" stamp.
    
    EXPERIMENTAL = 1
    # An "Experimental" stamp.
    
    NOT_APPROVED = 2
    # A "NotApproved" stamp.
    
    AS_IS = 3
    # An "AsIs" stamp.
    
    EXPIRED = 4
    # An "Expired" stamp.
    
    NOT_FOR_PUBLIC_RELEASE = 5
    # A "NotForPublicRelease" stamp.
    
    CONFIDENTIAL = 6
    # A "Confidential" stamp.
    
    FINAL = 7
    # A "Final" stamp.
    
    SOLD = 8
    # A "Sold" stamp.
    
    DEPARTMENTAL = 9
    # A "Departmental" stamp.
    
    FOR_COMMENT = 10
    # A "ForComment" stamp.
    
    TOP_SECRET = 11
    # A "TopSecret" stamp.
    
    DRAFT = 12
    # A "Draft" stamp.
    
    FOR_PUBLIC_RELEASE = 13
    # A "ForPublicRelease" stamp.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'PdfRubberStampIcon':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding PdfRubberStampIcon instance
            
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

__all__ = ['PdfRubberStampIcon']


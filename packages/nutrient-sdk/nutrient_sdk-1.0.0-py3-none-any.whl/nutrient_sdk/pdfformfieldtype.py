"""
Specifies the type of a PDF form field.
"""

from enum import Enum, auto
import ctypes

class PdfFormFieldType(Enum):
    """Specifies the type of a PDF form field.."""
    
    UNKNOWN = 0
    # Unknown or undefined field type.
    
    TEXT = 1
    # A text field where users can enter text from the keyboard.
    
    PUSH_BUTTON = 2
    # A push button that responds immediately to user input without retaining a permanent value.
    
    CHECK_BOX = 3
    # A check box that toggles between two states (on and off).
    
    RADIO_BUTTON = 4
    # A radio button that is part of a mutually exclusive group.
    
    COMBO_BOX = 5
    # A combo box (drop-down list), optionally with an editable text field.
    
    LIST_BOX = 6
    # A scrollable list box for selecting one or more items.
    
    SIGNATURE = 7
    # A signature field for electronic signatures.
    
    
    @classmethod
    def from_value(cls, value: int) -> 'PdfFormFieldType':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding PdfFormFieldType instance
            
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

__all__ = ['PdfFormFieldType']


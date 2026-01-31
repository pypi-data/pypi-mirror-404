"""
RectF struct module.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RectF:
    """
    Represents a rectangle with float coordinates.

    Attributes:
        left (float): The left coordinate of the rectangle.
        top (float): The top coordinate of the rectangle.
        right (float): The right coordinate of the rectangle.
        bottom (float): The bottom coordinate of the rectangle.
    """

    left: float
    top: float
    right: float
    bottom: float

    def __iter__(self):
        """Allow unpacking like tuple: x, y = vec2f(1.0, 2.0)"""
        yield self.left
        yield self.top
        yield self.right
        yield self.bottom

    def __repr__(self):
        """String representation of the struct."""
        return f"RectF(left={self.left}, top={self.top}, right={self.right}, bottom={self.bottom})"


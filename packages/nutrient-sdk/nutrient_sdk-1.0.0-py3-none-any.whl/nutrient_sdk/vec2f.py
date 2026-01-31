"""
vec2f struct module.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class vec2f:
    """
    Represents a 2D vector with X and Y components as floating-point values. Used to specify positions, sizes, and other 2D measurements in PDF coordinate space.

    Attributes:
        x (float): The X component in points.
        y (float): The Y component in points.
    """

    x: float
    y: float

    def __iter__(self):
        """Allow unpacking like tuple: x, y = vec2f(1.0, 2.0)"""
        yield self.x
        yield self.y

    def __repr__(self):
        """String representation of the struct."""
        return f"vec2f(x={self.x}, y={self.y})"


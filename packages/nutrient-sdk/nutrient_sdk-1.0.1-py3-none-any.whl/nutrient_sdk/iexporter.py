"""
Defines the contract for document exporters that convert documents to various output formats.
"""

from typing import Protocol, Optional, Any, Union, runtime_checkable
from abc import ABC, abstractmethod
import ctypes


@runtime_checkable
class IExporter(Protocol):
    """Defines the contract for document exporters that convert documents to various output formats.."""
    

class IExporterBase(ABC):
    """Defines the contract for document exporters that convert documents to various output formats.."""
    

__all__ = ['IExporter', 'IExporterBase']


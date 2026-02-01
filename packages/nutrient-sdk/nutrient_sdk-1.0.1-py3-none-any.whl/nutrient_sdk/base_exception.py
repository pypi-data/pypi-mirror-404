"""
Base exception classes for the Nutrient SDK.

All SDK-specific exceptions inherit from NutrientException.
"""

from typing import Optional, Any, Dict, List
import ctypes
import sys
import traceback
from datetime import datetime

class ErrorInfo(ctypes.Structure):
    """
    Structure to hold error information from native code.
    
    This structure is used to pass error details from the C++ SDK
    to Python exception handlers.
    """
    _fields_ = [
        ("code", ctypes.c_int),           # Numeric error code
        ("message", ctypes.c_char * 1024), # Error message
        ("source", ctypes.c_char * 256),   # Source location
        ("details", ctypes.c_char * 2048), # Additional details
    ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ErrorInfo to dictionary."""
        return {
            "code": self.code,
            "message": self.message.decode('utf-8', errors='replace') if self.message else "",
            "source": self.source.decode('utf-8', errors='replace') if self.source else "",
            "details": self.details.decode('utf-8', errors='replace') if self.details else "",
        }

class NutrientException(Exception):
    """
    Base exception class for all Nutrient SDK errors.
    
    This is the root of the SDK exception hierarchy. All SDK-specific
    exceptions should inherit from this class.
    
    Attributes:
        message: The error message
        error_code: Optional numeric error code from the native SDK
        error_source: Optional source location where the error occurred
        timestamp: When the exception was created
        context: Optional dictionary of additional context information
    
    Example:
        >>> try:
        ...     # SDK operation that might fail
        ...     document.export_as_pdf("output.pdf")
        ... except NutrientException as e:
        ...     print(f"SDK Error: {e}")
        ...     print(f"Error Code: {e.error_code}")
        ...     print(f"Source: {e.error_source}")
        ...     if e.has_native_error():
        ...         print(f"Native Details: {e.get_native_details()}")
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        error_source: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        """
        Initialize NutrientException.
        
        Args:
            message: The error message
            error_code: Optional numeric error code
            error_source: Optional source location of the error
            context: Optional context information
            **kwargs: Additional keyword arguments
        """
        super().__init__(message)
        self._message = message
        self._error_code = error_code
        self._error_source = error_source
        self._timestamp = datetime.now()
        self._context = context or {}
        self._native_error_info: Optional[ErrorInfo] = None
        
        for key, value in kwargs.items():
            if key not in self._context:
                self._context[key] = value
        
    
    @property
    def message(self) -> str:
        """Get the error message."""
        return self._message
    
    @property
    def error_code(self) -> Optional[int]:
        """Get the error code."""
        return self._error_code
    
    @property
    def error_source(self) -> Optional[str]:
        """Get the error source."""
        return self._error_source
    
    @property
    def timestamp(self) -> datetime:
        """Get when the exception was created."""
        return self._timestamp
    
    @property
    def context(self) -> Dict[str, Any]:
        """Get additional context information."""
        return self._context
    
    def set_native_error(self, error_info: ErrorInfo) -> None:
        """
        Associate native error information with this exception.
        
        Args:
            error_info: Error information from native SDK
        """
        self._native_error_info = error_info
        if error_info.code and not self._error_code:
            self._error_code = error_info.code
    
    def has_native_error(self) -> bool:
        """Check if this exception has associated native error information."""
        return self._native_error_info is not None
    
    def get_native_details(self) -> Optional[Dict[str, Any]]:
        """
        Get native error details if available.
        
        Returns:
            Dictionary with native error information or None
        """
        if self._native_error_info:
            return self._native_error_info.to_dict()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the exception to a dictionary representation.
        
        Returns:
            Dictionary containing all exception attributes
        """
        result = {
            "type": self.__class__.__name__,
            "message": self._message,
            "timestamp": self._timestamp.isoformat(),
        }
        
        if self._error_code is not None:
            result["error_code"] = self._error_code
        
        if self._error_source:
            result["error_source"] = self._error_source
        
        if self._context:
            result["context"] = self._context
        
        if self._native_error_info:
            result["native_error"] = self.get_native_details()
        
        
        return result
    
    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self._message]
        if self._error_code is not None:
            parts.append(f"(Error Code: {self._error_code})")
        if self._error_source:
            parts.append(f"[Source: {self._error_source}]")
        return " ".join(parts)
    
    def __repr__(self) -> str:
        """Detailed representation of the exception."""
        attrs = [f"message={repr(self._message)}"]
        if self._error_code is not None:
            attrs.append(f"error_code={self._error_code}")
        if self._error_source:
            attrs.append(f"error_source={repr(self._error_source)}")
        if self._context:
            attrs.append(f"context={repr(self._context)}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"

class SDKError(NutrientException):
    """
    General SDK error.
    
    This exception is raised for general SDK errors that don't
    fit into more specific exception categories.
    """
    pass

class InitializationError(NutrientException):
    """
    SDK initialization error.
    
    This exception is raised when the SDK fails to initialize properly,
    such as when the native library cannot be loaded or when required
    resources are missing.
    """
    pass

class LicenseError(NutrientException):
    """
    License validation error.
    
    This exception is raised when there are issues with the SDK license,
    such as an expired license, invalid license key, or missing license file.
    """
    pass

class DocumentError(NutrientException):
    """
    Document operation error.
    
    This exception is raised when document operations fail, such as
    opening, saving, or processing documents.
    """
    pass

class ConversionError(NutrientException):
    """
    File format conversion error.
    
    This exception is raised when converting between file formats fails,
    such as converting Word to PDF or PDF to HTML.
    """
    pass

class ValidationError(NutrientException):
    """
    Input validation error.
    
    This exception is raised when input validation fails, such as
    invalid parameters, out-of-range values, or malformed data.
    """
    pass

class IOError(NutrientException):
    """
    Input/Output operation error.
    
    This exception is raised when I/O operations fail, such as
    file not found, permission denied, or disk full errors.
    """
    pass

class MemoryError(NutrientException):
    """
    Memory allocation error.
    
    This exception is raised when the SDK cannot allocate required memory
    or when memory limits are exceeded.
    """
    pass

class TimeoutError(NutrientException):
    """
    Operation timeout error.
    
    This exception is raised when an operation takes longer than the
    specified timeout period.
    """
    pass

class NotImplementedError(NutrientException):
    """
    Feature not implemented error.
    
    This exception is raised when attempting to use a feature that
    is not yet implemented in the current SDK version.
    """
    pass

class PermissionError(NutrientException):
    """
    Permission denied error.
    
    This exception is raised when the SDK lacks necessary permissions
    to perform an operation, such as accessing protected files or
    system resources.
    """
    pass

def handle_native_error(error_info: ErrorInfo, default_exception_class=SDKError) -> None:
    """
    Convert native error information to a Python exception and raise it.
    
    Args:
        error_info: Error information from native SDK
        default_exception_class: Exception class to use if specific type cannot be determined
        
    Raises:
        Appropriate NutrientException subclass based on error code
    """
    if not error_info or error_info.code == 0:
        return  # No error
    
    message = error_info.message.decode('utf-8', errors='replace') if error_info.message else "Unknown error"
    source = error_info.source.decode('utf-8', errors='replace') if error_info.source else None
    error_code = error_info.code
    exception_class = default_exception_class

    if 1000 <= error_code < 2000:
        exception_class = InitializationError
    elif 2000 <= error_code < 3000:
        exception_class = LicenseError
    elif 3000 <= error_code < 4000:
        exception_class = DocumentError
    elif 4000 <= error_code < 5000:
        exception_class = ConversionError
    elif 5000 <= error_code < 6000:
        exception_class = ValidationError
    elif 6000 <= error_code < 7000:
        exception_class = IOError
    elif 7000 <= error_code < 8000:
        exception_class = MemoryError
    elif 8000 <= error_code < 9000:
        exception_class = TimeoutError
    elif 9000 <= error_code < 10000:
        exception_class = NotImplementedError
    elif 10000 <= error_code < 11000:
        exception_class = PermissionError

    exc = exception_class(
        message=message,
        error_code=error_code,
        error_source=source
    )
    exc.set_native_error(error_info)
    raise exc

__all__ = [
    'ErrorInfo',
    'NutrientException',
    'SDKError',
    'InitializationError',
    'LicenseError',
    'DocumentError',
    'ConversionError',
    'ValidationError',
    'IOError',
    'MemoryError',
    'TimeoutError',
    'NotImplementedError',
    'PermissionError',
    'handle_native_error',
]
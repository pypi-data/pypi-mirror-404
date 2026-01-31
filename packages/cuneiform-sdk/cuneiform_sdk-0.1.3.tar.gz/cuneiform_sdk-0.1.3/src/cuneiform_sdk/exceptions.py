"""
Exception hierarchy for Cuneiform SDK.
"""

from typing import Optional, Dict, Any


class CuneiformError(Exception):
    """Base exception for all Cuneiform SDK errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}


class ValidationError(CuneiformError):
    """Raised when data validation fails."""
    pass


class DatasetError(CuneiformError):
    """Raised when dataset operations fail."""
    pass


class FunctionRegistrationError(CuneiformError):
    """Raised when function registration fails."""
    pass


class ContextError(CuneiformError):
    """Raised when workflow context operations fail."""
    pass
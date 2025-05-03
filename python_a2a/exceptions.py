"""
Custom exceptions for the A2A protocol.
"""

class A2AError(Exception):
    """Base exception for all A2A errors"""
    pass


class A2AImportError(A2AError):
    """Raised when a required package is not installed"""
    pass


class A2AConnectionError(A2AError):
    """Raised when connection to an agent or service fails"""
    pass


class A2AResponseError(A2AError):
    """Raised when an agent returns an invalid response"""
    pass


class A2ARequestError(A2AError):
    """Raised when an incoming request is invalid"""
    pass


class A2AValidationError(A2AError):
    """Raised when a message or conversation fails validation"""
    pass


class A2AAuthenticationError(A2AError):
    """Raised when authentication fails"""
    pass


class A2AConfigurationError(A2AError):
    """Raised when configuration is invalid"""
    pass


class A2AStreamingError(A2AError):
    """Raised when a streaming operation fails"""
    pass
"""
Tests for the exceptions module.
"""

import pytest

from python_a2a import (
    A2AError,
    A2AImportError,
    A2AConnectionError,
    A2AResponseError,
    A2ARequestError,
    A2AValidationError,
    A2AAuthenticationError,
    A2AConfigurationError
)


class TestExceptions:
    def test_error_hierarchy(self):
        """Test that all exceptions inherit from A2AError"""
        assert issubclass(A2AImportError, A2AError)
        assert issubclass(A2AConnectionError, A2AError)
        assert issubclass(A2AResponseError, A2AError)
        assert issubclass(A2ARequestError, A2AError)
        assert issubclass(A2AValidationError, A2AError)
        assert issubclass(A2AAuthenticationError, A2AError)
        assert issubclass(A2AConfigurationError, A2AError)
    
    def test_error_message(self):
        """Test that error messages are properly stored"""
        error = A2AError("Test error message")
        assert str(error) == "Test error message"
        
        import_error = A2AImportError("Missing package")
        assert str(import_error) == "Missing package"
    
    def test_exception_catching(self):
        """Test catching exceptions by base type"""
        # Function that raises different types of errors
        def raise_error(error_type):
            if error_type == "import":
                raise A2AImportError("Import error")
            elif error_type == "connection":
                raise A2AConnectionError("Connection error")
            elif error_type == "validation":
                raise A2AValidationError("Validation error")
        
        # Should catch specific error types
        with pytest.raises(A2AImportError):
            raise_error("import")
        
        with pytest.raises(A2AConnectionError):
            raise_error("connection")
        
        # Should also catch by base type
        with pytest.raises(A2AError):
            raise_error("import")
        
        with pytest.raises(A2AError):
            raise_error("validation")
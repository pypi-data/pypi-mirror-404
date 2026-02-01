"""
Comprehensive tests for the security error handling framework.
Tests SecureErrorHandler class and secure error handling decorators.
"""

import pytest
import tempfile
import os
import logging
import re
import time
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.security.error_handling import (
    SecureErrorHandler,
    ErrorLevel,
    secure_error_handler,
    secure_error_handling,
    constant_time_compare,
    timing_safe_operation
)


class TestErrorLevel:
    """Test ErrorLevel enumeration."""
    
    def test_error_level_values(self):
        """Test that ErrorLevel has correct values."""
        assert ErrorLevel.PUBLIC.value == "public"
        assert ErrorLevel.INTERNAL.value == "internal"
        assert ErrorLevel.SECURITY.value == "security"
    
    def test_error_level_membership(self):
        """Test ErrorLevel membership."""
        levels = [ErrorLevel.PUBLIC, ErrorLevel.INTERNAL, ErrorLevel.SECURITY]
        assert len(levels) == 3
        
        for level in levels:
            assert isinstance(level, ErrorLevel)


class TestSecureErrorHandler:
    """Test SecureErrorHandler class."""
    
    @pytest.fixture
    def error_handler(self):
        """Create a SecureErrorHandler instance for testing."""
        with patch('dtPyAppFramework.paths.ApplicationPaths') as mock_paths, \
             patch('dtPyAppFramework.security.filesystem.SecureFileManager.create_secure_file') as mock_create:
            
            # Mock ApplicationPaths to return a safe directory
            mock_app_paths = MagicMock()
            mock_app_paths.app_data_root_path = '/tmp/test_security_logs'
            mock_paths.return_value = mock_app_paths
            
            # Mock SecureFileManager to avoid actual file creation
            mock_create.return_value = '/tmp/test_security_logs/security_audit.log'
            
            return SecureErrorHandler()
    
    @pytest.fixture
    def mock_loggers(self, error_handler):
        """Mock the loggers to capture log calls."""
        with patch.object(error_handler, 'public_logger') as mock_public, \
             patch.object(error_handler, 'internal_logger') as mock_internal, \
             patch.object(error_handler, 'security_logger') as mock_security:
            yield mock_public, mock_internal, mock_security
    
    def test_error_handler_initialization(self, error_handler):
        """Test SecureErrorHandler initialization."""
        assert hasattr(error_handler, 'public_logger')
        assert hasattr(error_handler, 'internal_logger')
        assert hasattr(error_handler, 'security_logger')
    
    def test_log_secret_operation_error(self, error_handler, mock_loggers):
        """Test logging of secret operation errors."""
        mock_public, mock_internal, mock_security = mock_loggers
        
        operation = "set_secret"
        key = "test_key"
        error = ValueError("Test error")
        store_name = "test_store"
        
        error_id = error_handler.log_secret_operation_error(
            operation, key, error, store_name
        )
        
        # Verify error ID format
        assert isinstance(error_id, str)
        assert len(error_id) == 16  # 8 bytes hex = 16 characters
        assert re.match(r'^[a-f0-9]{16}$', error_id)
        
        # Verify public log (minimal info)
        mock_public.error.assert_called_once()
        public_call = mock_public.error.call_args[0][0]
        assert "Secret operation 'set_secret' failed" in public_call
        assert error_id in public_call
        assert "test_key" not in public_call  # No sensitive info
        
        # Verify internal log (hashed info)
        mock_internal.error.assert_called_once()
        internal_call = mock_internal.error.call_args[0][0]
        assert error_id in internal_call
        assert operation in internal_call
        assert store_name in internal_call
        assert "KeyHash:" in internal_call
        assert "test_key" not in internal_call  # Key should be hashed
        
        # Verify security log (full details)
        mock_security.error.assert_called_once()
        security_call = mock_security.error.call_args[0][0]
        assert error_id in security_call
        assert operation in security_call
        assert store_name in security_call
        assert "test_key" in security_call  # Full key in security log
        assert "ValueError" in security_call
        assert "Test error" in security_call
    
    def test_log_secret_operation_error_no_key(self, error_handler, mock_loggers):
        """Test logging when key is None or empty."""
        mock_public, mock_internal, _mock_security = mock_loggers
        
        operation = "operation_without_key"
        error = RuntimeError("No key error")
        
        error_id = error_handler.log_secret_operation_error(
            operation, None, error
        )
        
        # Verify public log uses generic message
        public_call = mock_public.error.call_args[0][0]
        assert "Secret store operation failed" in public_call
        assert error_id in public_call
        
        # Verify internal log uses "unknown" for missing key
        internal_call = mock_internal.error.call_args[0][0]
        assert "KeyHash: unknown" in internal_call
    
    def test_log_authentication_error(self, error_handler, mock_loggers):
        """Test logging of authentication errors."""
        mock_public, mock_internal, mock_security = mock_loggers
        
        operation = "keystore_access"
        target = "test.v3keystore"
        error = PermissionError("Access denied")
        
        error_id = error_handler.log_authentication_error(operation, target, error)
        
        # Verify error ID
        assert isinstance(error_id, str)
        assert len(error_id) == 16
        
        # Verify public log (minimal info)
        mock_public.error.assert_called_once()
        public_call = mock_public.error.call_args[0][0]
        assert f"Authentication failed for {operation}" in public_call
        assert error_id in public_call
        assert target not in public_call  # No sensitive target info
        
        # Verify internal log (operation info)
        mock_internal.error.assert_called_once()
        internal_call = mock_internal.error.call_args[0][0]
        assert error_id in internal_call
        assert operation in internal_call
        assert target in internal_call
        assert "PermissionError" in internal_call
        
        # Verify security log (full details)
        mock_security.error.assert_called_once()
        security_call = mock_security.error.call_args[0][0]
        assert error_id in security_call
        assert operation in security_call
        assert target in security_call
        assert "PermissionError: Access denied" in security_call
    
    def test_log_file_operation_error(self, error_handler, mock_loggers):
        """Test logging of file operation errors."""
        mock_public, mock_internal, mock_security = mock_loggers
        
        operation = "secure_file_create"
        file_path = "/tmp/sensitive_file.txt"
        error = OSError("Disk full")
        
        error_id = error_handler.log_file_operation_error(operation, file_path, error)
        
        # Verify error ID
        assert isinstance(error_id, str)
        assert len(error_id) == 16
        
        # Verify public log (minimal info)
        mock_public.error.assert_called_once()
        public_call = mock_public.error.call_args[0][0]
        assert f"File operation '{operation}' failed" in public_call
        assert error_id in public_call
        assert file_path not in public_call  # No sensitive path info
        
        # Verify internal log (hashed path)
        mock_internal.error.assert_called_once()
        internal_call = mock_internal.error.call_args[0][0]
        assert error_id in internal_call
        assert operation in internal_call
        assert "PathHash:" in internal_call
        assert file_path not in internal_call  # Path should be hashed
        
        # Verify security log (full details)
        mock_security.error.assert_called_once()
        security_call = mock_security.error.call_args[0][0]
        assert error_id in security_call
        assert operation in security_call
        assert file_path in security_call  # Full path in security log
        assert "OSError: Disk full" in security_call
    
    def test_multiple_error_logging(self, error_handler, mock_loggers):
        """Test that multiple errors get different correlation IDs."""
        _mock_public, _mock_internal, _mock_security = mock_loggers
        
        error1_id = error_handler.log_secret_operation_error(
            "op1", "key1", ValueError("Error 1")
        )
        error2_id = error_handler.log_authentication_error(
            "op2", "target2", RuntimeError("Error 2")
        )
        error3_id = error_handler.log_file_operation_error(
            "op3", "/path3", OSError("Error 3")
        )
        
        # All error IDs should be different
        assert error1_id != error2_id
        assert error2_id != error3_id
        assert error1_id != error3_id
        
        # All should be valid hex strings
        for error_id in [error1_id, error2_id, error3_id]:
            assert re.match(r'^[a-f0-9]{16}$', error_id)


class TestSecureErrorHandlingDecorator:
    """Test the secure_error_handling decorator."""
    
    def test_decorator_with_normal_execution(self):
        """Test decorator allows normal execution."""
        
        @secure_error_handling("test_operation")
        def normal_function(x, y):
            return x + y
        
        result = normal_function(2, 3)
        assert result == 5
    
    def test_decorator_with_generic_exception(self):
        """Test decorator handles generic exceptions."""
        
        @secure_error_handling("test_operation")
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError) as exc_info:
            failing_function()
        
        # Error message should include correlation ID
        error_msg = str(exc_info.value)
        assert "Operation failed (ID:" in error_msg
        assert re.search(r'ID: [a-f0-9]{16}\)', error_msg)
    
    def test_decorator_with_security_validation_error(self):
        """Test decorator handles SecurityValidationError specifically."""
        from dtPyAppFramework.security.validation import SecurityValidationError
        
        @secure_error_handling("test_operation")
        def validation_failing_function():
            raise SecurityValidationError("Validation failed", field="test_field")
        
        with pytest.raises(SecurityValidationError) as exc_info:
            validation_failing_function()
        
        # Should get ValidationError with correlation ID
        error_msg = str(exc_info.value)
        assert "Validation failed (ID:" in error_msg
        assert re.search(r'ID: [a-f0-9]{16}\)', error_msg)
    
    def test_decorator_with_filesystem_security_error(self):
        """Test decorator handles FileSystemSecurityError specifically."""
        from dtPyAppFramework.security.filesystem import FileSystemSecurityError
        
        @secure_error_handling("test_operation")
        def filesystem_failing_function():
            raise FileSystemSecurityError("File operation failed")
        
        with pytest.raises(FileSystemSecurityError) as exc_info:
            filesystem_failing_function()
        
        # Should get FileSystemSecurityError with correlation ID
        error_msg = str(exc_info.value)
        assert "File operation failed (ID:" in error_msg
        assert re.search(r'ID: [a-f0-9]{16}\)', error_msg)
    
    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves original function metadata."""
        
        @secure_error_handling("test_operation")
        def documented_function(x, y):
            """This function adds two numbers."""
            return x + y
        
        assert documented_function.__name__ == "documented_function"
        assert "adds two numbers" in documented_function.__doc__
    
    def test_decorator_with_args_and_kwargs(self):
        """Test decorator works with various function signatures."""
        
        @secure_error_handling("test_operation")
        def complex_function(a, b, *args, c=None, **kwargs):
            return {"a": a, "b": b, "args": args, "c": c, "kwargs": kwargs}
        
        result = complex_function(1, 2, 3, 4, c=5, d=6, e=7)
        expected = {"a": 1, "b": 2, "args": (3, 4), "c": 5, "kwargs": {"d": 6, "e": 7}}
        assert result == expected


class TestConstantTimeCompare:
    """Test constant-time comparison function."""
    
    def test_equal_bytes(self):
        """Test comparison of equal byte strings."""
        data1 = b"hello world"
        data2 = b"hello world"
        
        result = constant_time_compare(data1, data2)
        assert result is True
    
    def test_different_bytes(self):
        """Test comparison of different byte strings."""
        data1 = b"hello world"
        data2 = b"hello earth"
        
        result = constant_time_compare(data1, data2)
        assert result is False
    
    def test_different_lengths(self):
        """Test comparison of different length byte strings."""
        data1 = b"hello"
        data2 = b"hello world"
        
        result = constant_time_compare(data1, data2)
        assert result is False
    
    def test_empty_bytes(self):
        """Test comparison of empty byte strings."""
        data1 = b""
        data2 = b""
        
        result = constant_time_compare(data1, data2)
        assert result is True
        
        # One empty, one not
        result = constant_time_compare(b"", b"hello")
        assert result is False
    
    def test_constant_time_property(self):
        """Test that function takes roughly constant time for same-length inputs."""
        import time

        # Use multiple iterations to reduce noise from scheduling jitter,
        # especially on shared CI runners where CPU contention is common.
        iterations = 1000
        data1 = b"x" * 1000
        data2 = b"x" * 1000  # Same
        data3 = b"y" * 1000  # Different

        # Time equal comparison
        start = time.perf_counter()
        for _ in range(iterations):
            result1 = constant_time_compare(data1, data2)
        time1 = time.perf_counter() - start

        # Time different comparison
        start = time.perf_counter()
        for _ in range(iterations):
            result2 = constant_time_compare(data1, data3)
        time2 = time.perf_counter() - start

        assert result1 is True
        assert result2 is False

        # Times should be similar; allow up to 3x variance to avoid flaky
        # failures on busy CI runners while still catching gross timing leaks.
        time_ratio = max(time1, time2) / min(time1, time2)
        assert time_ratio < 3.0


class TestTimingSafeOperation:
    """Test timing-safe operation wrapper."""
    
    def test_timing_safe_normal_operation(self):
        """Test timing-safe wrapper with normal operation."""
        
        def fast_operation():
            return "result"
        
        start_time = time.time()
        result = timing_safe_operation(fast_operation, min_time=0.1)
        elapsed = time.time() - start_time
        
        assert result == "result"
        assert elapsed >= 0.1  # Should take at least minimum time
    
    def test_timing_safe_slow_operation(self):
        """Test timing-safe wrapper with slow operation."""
        import time
        
        def slow_operation():
            time.sleep(0.15)  # Longer than min_time
            return "slow_result"
        
        start_time = time.time()
        result = timing_safe_operation(slow_operation, min_time=0.1)
        elapsed = time.time() - start_time
        
        assert result == "slow_result"
        assert elapsed >= 0.15  # Should take actual operation time
    
    def test_timing_safe_operation_with_exception(self):
        """Test timing-safe wrapper handles exceptions while maintaining timing."""
        import time
        
        def failing_operation():
            raise ValueError("Operation failed")
        
        start_time = time.time()
        
        with pytest.raises(ValueError):
            timing_safe_operation(failing_operation, min_time=0.1)
        
        elapsed = time.time() - start_time
        assert elapsed >= 0.1  # Should still take minimum time even on error
    
    def test_timing_safe_different_min_times(self):
        """Test timing-safe wrapper with different minimum times."""
        import time
        
        def quick_operation():
            return "quick"
        
        # Test with 0.05 second minimum
        start_time = time.time()
        result = timing_safe_operation(quick_operation, min_time=0.05)
        elapsed = time.time() - start_time
        
        assert result == "quick"
        assert elapsed >= 0.05
        assert elapsed < 0.1  # Should not take much longer than required


class TestGlobalErrorHandler:
    """Test the global secure_error_handler instance."""
    
    def test_global_instance_exists(self):
        """Test that global error handler instance exists."""
        assert secure_error_handler is not None
        assert isinstance(secure_error_handler, SecureErrorHandler)
    
    def test_global_instance_functionality(self):
        """Test that global error handler works correctly."""
        # This is a basic smoke test
        error_id = secure_error_handler.log_secret_operation_error(
            "test_operation", 
            "test_key", 
            RuntimeError("Test error"),
            "test_store"
        )
        
        assert isinstance(error_id, str)
        assert len(error_id) == 16
        assert re.match(r'^[a-f0-9]{16}$', error_id)


class TestErrorHandlingIntegration:
    """Test integration scenarios and edge cases."""
    
    def test_error_correlation_across_components(self):
        """Test that errors can be correlated across different components."""
        error_handler = SecureErrorHandler()
        
        # Simulate errors from different components
        secret_error_id = error_handler.log_secret_operation_error(
            "get_secret", "api_key", ValueError("Key not found"), "local_store"
        )
        
        file_error_id = error_handler.log_file_operation_error(
            "read_keystore", "/path/to/keystore", OSError("File locked"), 
        )
        
        auth_error_id = error_handler.log_authentication_error(
            "keystore_unlock", "encrypted_keystore", PermissionError("Wrong password")
        )
        
        # All should have different IDs but be trackable
        all_ids = [secret_error_id, file_error_id, auth_error_id]
        assert len(set(all_ids)) == 3  # All unique
        
        for error_id in all_ids:
            assert len(error_id) == 16
            assert re.match(r'^[a-f0-9]{16}$', error_id)
    
    def test_error_handler_with_unicode(self):
        """Test error handler works with Unicode content."""
        error_handler = SecureErrorHandler()
        
        unicode_key = "clé_secrète_🔑"
        unicode_error = ValueError("Erreur unicode: données invalides")
        
        error_id = error_handler.log_secret_operation_error(
            "unicode_operation", unicode_key, unicode_error, "unicode_store"
        )
        
        assert isinstance(error_id, str)
        assert len(error_id) == 16
    
    def test_error_handler_with_large_data(self):
        """Test error handler with large error messages."""
        error_handler = SecureErrorHandler()
        
        large_error_msg = "Error: " + "x" * 10000  # 10KB error message
        large_error = RuntimeError(large_error_msg)
        
        error_id = error_handler.log_secret_operation_error(
            "large_data_operation", "large_key", large_error, "large_store"
        )
        
        assert isinstance(error_id, str)
        assert len(error_id) == 16
    
    def test_error_handler_with_none_values(self):
        """Test error handler handles None values gracefully."""
        error_handler = SecureErrorHandler()
        
        # Test with None store name (omit argument to use default None)
        error_id1 = error_handler.log_secret_operation_error(
            "none_test", "test_key", ValueError("Test")
        )
        
        # Test with empty key
        error_id2 = error_handler.log_secret_operation_error(
            "empty_key_test", "", ValueError("Test"), "test_store"
        )
        
        assert isinstance(error_id1, str)
        assert isinstance(error_id2, str)
        assert error_id1 != error_id2


if __name__ == "__main__":
    pytest.main([__file__])
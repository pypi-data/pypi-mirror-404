"""
Comprehensive tests for the security input validation framework.
Tests SecurityValidationError and InputValidator classes.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.security.validation import (
    InputValidator, 
    SecurityValidationError
)


class TestSecurityValidationError:
    """Test SecurityValidationError exception class."""
    
    def test_basic_exception(self):
        """Test basic exception creation."""
        error = SecurityValidationError("Test message")
        assert str(error) == "Test message"
        assert error.field is None
        assert error.value_hash is None
    
    def test_exception_with_field(self):
        """Test exception with field information."""
        error = SecurityValidationError("Test message", field="test_field")
        assert str(error) == "Test message"
        assert error.field == "test_field"
        assert error.value_hash is None
    
    def test_exception_with_value_hash(self):
        """Test exception with value hash."""
        error = SecurityValidationError("Test message", field="test_field", value="test_value")
        assert str(error) == "Test message"
        assert error.field == "test_field"
        assert error.value_hash is not None
        assert len(error.value_hash) == 8  # First 8 chars of hash


class TestInputValidatorSecretKeys:
    """Test InputValidator.validate_secret_key method."""
    
    def test_valid_secret_keys(self):
        """Test validation of valid secret keys."""
        valid_keys = [
            "simple_key",
            "key123",
            "key.with.dots",
            "key-with-dashes",
            "key_with_underscores",
            "MixedCaseKey",
            "a",  # Single character
            "a" * 255,  # Maximum length
            "api.database.password",
            "service-1.auth-token",
            "user_123.session_key"
        ]
        
        for key in valid_keys:
            result = InputValidator.validate_secret_key(key)
            assert result == key, f"Valid key '{key}' should pass validation"
    
    def test_invalid_secret_key_types(self):
        """Test validation with invalid types."""
        invalid_inputs = [None, 123, [], {}, True, 3.14]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_secret_key(invalid_input)
            assert "must be string" in str(exc_info.value)
    
    def test_empty_secret_keys(self):
        """Test validation of empty or whitespace-only keys."""
        empty_keys = ["", "   ", "\t", "\n", "\r\n"]
        
        for key in empty_keys:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_secret_key(key)
            assert "cannot be empty" in str(exc_info.value)
    
    def test_key_length_limits(self):
        """Test secret key length validation."""
        # Too long
        with pytest.raises(SecurityValidationError) as exc_info:
            InputValidator.validate_secret_key("a" * 256)
        assert "too long" in str(exc_info.value)
    
    def test_path_traversal_detection(self):
        """Test detection of path traversal attempts."""
        traversal_keys = [
            "../secret",
            "..\\secret",
            "secret/../other",
            "secret\\..\\other",
            "../",
            "..\\",
            "secret/..",
            "secret\\.."
        ]
        
        for key in traversal_keys:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_secret_key(key)
            assert "Path traversal detected" in str(exc_info.value)
    
    def test_invalid_characters(self):
        """Test rejection of invalid characters."""
        # Note: SAFE_KEY_PATTERN allows a-zA-Z0-9._/- so those are valid
        invalid_keys = [
            "key with spaces",
            "key@invalid",
            "key#invalid",
            "key$invalid",
            "key%invalid",
            "key^invalid",
            "key&invalid",
            "key*invalid",
            "key(invalid)",
            "key[invalid]",
            "key{invalid}",
            "key|invalid",
            "key\\invalid",
            "key:invalid",
            "key;invalid",
            "key<invalid>",
            "key?invalid",
            "key+invalid",
            "key=invalid"
        ]
        
        for key in invalid_keys:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_secret_key(key)
            assert "Invalid characters" in str(exc_info.value)
    
    def test_reserved_names(self):
        """Test rejection of Windows reserved names."""
        reserved_names = [
            "con", "CON", "Con",
            "prn", "PRN", "Prn", 
            "aux", "AUX", "Aux",
            "nul", "NUL", "Nul",
            "com1", "COM1", "Com1",
            "lpt1", "LPT1", "Lpt1",
            "com9", "lpt9"
        ]
        
        for name in reserved_names:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_secret_key(name)
            assert "Reserved key name" in str(exc_info.value)


class TestInputValidatorSecretValues:
    """Test InputValidator.validate_secret_value method."""
    
    def test_valid_secret_values(self):
        """Test validation of valid secret values."""
        valid_values = [
            "simple_value",
            "password123!",
            "very_long_secret_value_with_lots_of_characters",
            "value with spaces",
            "special@#$%^&*()characters",
            "multiline\nvalue\nhere",
            "unicode_value_héllo_🔑",
            '{"json": "value"}',
            "SGVsbG8gV29ybGQ="  # base64
        ]
        
        for value in valid_values:
            result = InputValidator.validate_secret_value(value)
            assert result == value, "Valid value should pass validation"
    
    def test_invalid_secret_value_types(self):
        """Test validation with invalid types."""
        invalid_inputs = [None, 123, [], {}, True, 3.14]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_secret_value(invalid_input)
            assert "must be string" in str(exc_info.value)
    
    def test_empty_secret_values(self):
        """Test validation of empty values."""
        with pytest.raises(SecurityValidationError) as exc_info:
            InputValidator.validate_secret_value("")
        assert "cannot be empty" in str(exc_info.value)
    
    def test_secret_value_size_limits(self):
        """Test secret value size validation."""
        # Default max size (64KB)
        large_value = "x" * (64 * 1024 + 1)
        with pytest.raises(SecurityValidationError) as exc_info:
            InputValidator.validate_secret_value(large_value)
        assert "too large" in str(exc_info.value)
        
        # Custom max size
        medium_value = "x" * 1001
        with pytest.raises(SecurityValidationError) as exc_info:
            InputValidator.validate_secret_value(medium_value, max_size=1000)
        assert "too large" in str(exc_info.value)
    
    def test_script_injection_detection(self):
        """Test detection of potential script injection."""
        # This should log warnings but not fail validation
        suspicious_values = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "onload=alert(1)",
            "eval(malicious_code)"
        ]
        
        # These should pass validation but log warnings
        for value in suspicious_values:
            result = InputValidator.validate_secret_value(value)
            assert result == value


class TestInputValidatorFilePaths:
    """Test InputValidator.validate_file_path method."""
    
    def test_valid_file_paths(self):
        """Test validation of valid file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_paths = [
                os.path.join(temp_dir, "test.txt"),
                os.path.join(temp_dir, "subdir", "test.txt"),
                temp_dir,
                "/absolute/path/file.txt",
                "relative/path/file.txt"
            ]
            
            for path in valid_paths:
                result = InputValidator.validate_file_path(path)
                assert isinstance(result, Path)
    
    def test_invalid_file_path_types(self):
        """Test validation with invalid types."""
        invalid_inputs = [None, 123, [], {}, True, 3.14]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_file_path(invalid_input)
            assert "must be string" in str(exc_info.value)
    
    def test_empty_file_paths(self):
        """Test validation of empty paths."""
        empty_paths = ["", "   ", "\t"]
        
        for path in empty_paths:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_file_path(path)
            assert "cannot be empty" in str(exc_info.value)
    
    def test_path_traversal_detection(self):
        """Test detection of path traversal in file paths."""
        traversal_paths = [
            "../secret.txt",
            "..\\secret.txt",
            "path/../other.txt",
            "path\\..\\other.txt"
        ]
        
        for path in traversal_paths:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_file_path(path)
            assert "Path traversal detected" in str(exc_info.value)
    
    def test_allowed_directories_restriction(self):
        """Test file path restriction to allowed directories."""
        with tempfile.TemporaryDirectory() as allowed_dir:
            with tempfile.TemporaryDirectory() as forbidden_dir:
                
                # Should pass - within allowed directory
                allowed_file = os.path.join(allowed_dir, "allowed.txt")
                result = InputValidator.validate_file_path(
                    allowed_file, 
                    allowed_dirs=[allowed_dir]
                )
                assert isinstance(result, Path)
                
                # Should fail - outside allowed directory
                forbidden_file = os.path.join(forbidden_dir, "forbidden.txt")
                with pytest.raises(SecurityValidationError) as exc_info:
                    InputValidator.validate_file_path(
                        forbidden_file, 
                        allowed_dirs=[allowed_dir]
                    )
                assert "not in allowed directories" in str(exc_info.value)


class TestInputValidatorYAMLContent:
    """Test InputValidator.validate_yaml_content method."""
    
    def test_valid_yaml_content(self):
        """Test validation of valid YAML content."""
        valid_yaml = [
            "key: value",
            "list:\n  - item1\n  - item2",
            "nested:\n  key: value",
            "simple_string",
            "123",
            "true"
        ]
        
        for content in valid_yaml:
            result = InputValidator.validate_yaml_content(content)
            assert result == content
    
    def test_invalid_yaml_content_types(self):
        """Test validation with invalid types."""
        invalid_inputs = [None, 123, [], {}, True, 3.14]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_yaml_content(invalid_input)
            assert "must be string" in str(exc_info.value)
    
    def test_yaml_content_size_limits(self):
        """Test YAML content size validation."""
        # Large content exceeding default limit
        large_content = "x" * (10 * 1024 * 1024 + 1)
        with pytest.raises(SecurityValidationError) as exc_info:
            InputValidator.validate_yaml_content(large_content)
        assert "too large" in str(exc_info.value)
        
        # Custom size limit
        medium_content = "x" * 1001
        with pytest.raises(SecurityValidationError) as exc_info:
            InputValidator.validate_yaml_content(medium_content, max_size=1000)
        assert "too large" in str(exc_info.value)
    
    def test_billion_laughs_detection(self):
        """Test detection of billion laughs attack patterns."""
        # Too many entity references
        entity_content = "&" * 101
        with pytest.raises(SecurityValidationError) as exc_info:
            InputValidator.validate_yaml_content(entity_content)
        assert "Excessive YAML references" in str(exc_info.value)
        
        # Too many anchor references  
        anchor_content = "*" * 101
        with pytest.raises(SecurityValidationError) as exc_info:
            InputValidator.validate_yaml_content(anchor_content)
        assert "Excessive YAML references" in str(exc_info.value)
    
    def test_suspicious_pattern_detection(self):
        """Test detection of suspicious patterns in YAML."""
        # These should pass validation but log warnings
        suspicious_patterns = [
            "eval: something",
            "exec: command",
            "import: module", 
            "__import__: builtin",
            "subprocess: call",
            "os.system: command"
        ]
        
        for pattern in suspicious_patterns:
            result = InputValidator.validate_yaml_content(pattern)
            assert result == pattern  # Should pass but log warning


class TestInputValidatorConfigurationKeys:
    """Test InputValidator.validate_configuration_key method."""
    
    def test_valid_configuration_keys(self):
        """Test validation of valid configuration keys."""
        valid_keys = [
            "database.host",
            "app.name", 
            "logging.level",
            "secrets.azure.vault_url",
            "multiprocessing.max_workers",
            "simple_key",
            "key123",
            "key-with-dashes",
            "key_with_underscores"
        ]
        
        for key in valid_keys:
            result = InputValidator.validate_configuration_key(key)
            assert result == key
    
    def test_invalid_configuration_key_types(self):
        """Test validation with invalid types."""
        invalid_inputs = [None, 123, [], {}, True, 3.14]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_configuration_key(invalid_input)
            assert "must be string" in str(exc_info.value)
    
    def test_empty_configuration_keys(self):
        """Test validation of empty keys."""
        empty_keys = ["", "   ", "\t"]
        
        for key in empty_keys:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_configuration_key(key)
            assert "cannot be empty" in str(exc_info.value)
    
    def test_configuration_key_length_limits(self):
        """Test configuration key length validation."""
        # Too long
        long_key = "a" * 501
        with pytest.raises(SecurityValidationError) as exc_info:
            InputValidator.validate_configuration_key(long_key)
        assert "too long" in str(exc_info.value)
    
    def test_invalid_configuration_key_characters(self):
        """Test rejection of invalid characters in config keys."""
        invalid_keys = [
            "key with spaces",
            "key@invalid",
            "key#invalid", 
            "key$invalid",
            "key%invalid",
            "key^invalid",
            "key&invalid",
            "key*invalid",
            "key(invalid)",
            "key[invalid]",
            "key{invalid}",
            "key|invalid",
            "key\\invalid",
            "key/invalid",
            "key:invalid",
            "key;invalid",
            "key<invalid>",
            "key?invalid",
            "key+invalid",
            "key=invalid"
        ]
        
        for key in invalid_keys:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_configuration_key(key)
            assert "Invalid characters" in str(exc_info.value)
    
    def test_invalid_dot_usage(self):
        """Test rejection of invalid dot usage in config keys."""
        invalid_dot_keys = [
            ".key",          # Leading dot
            "key.",          # Trailing dot
            "key..subkey",   # Double dots
            "key...subkey",  # Triple dots
            ".key.subkey",   # Leading dot with subkey
            "key.subkey."    # Trailing dot with subkey
        ]
        
        for key in invalid_dot_keys:
            with pytest.raises(SecurityValidationError) as exc_info:
                InputValidator.validate_configuration_key(key)
            assert "Invalid dot usage" in str(exc_info.value)


class TestInputValidatorEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_unicode_handling(self):
        """Test proper Unicode handling."""
        unicode_key = "test_key_héllo_🔑"
        
        # Should pass for secret values
        result = InputValidator.validate_secret_value(unicode_key)
        assert result == unicode_key
        
        # Should fail for secret keys (invalid characters)
        with pytest.raises(SecurityValidationError):
            InputValidator.validate_secret_key(unicode_key)
    
    def test_boundary_lengths(self):
        """Test boundary length conditions."""
        # Exactly at limit for secret key
        key_255 = "a" * 255
        result = InputValidator.validate_secret_key(key_255)
        assert result == key_255
        
        # Exactly at limit for config key
        config_500 = "a" * 500
        result = InputValidator.validate_configuration_key(config_500)
        assert result == config_500
    
    def test_normalization(self):
        """Test path normalization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Path with redundant separators
            redundant_path = os.path.join(temp_dir, "subdir", "..", "file.txt")
            
            # Should normalize but detect traversal
            with pytest.raises(SecurityValidationError):
                InputValidator.validate_file_path(redundant_path)


if __name__ == "__main__":
    pytest.main([__file__])
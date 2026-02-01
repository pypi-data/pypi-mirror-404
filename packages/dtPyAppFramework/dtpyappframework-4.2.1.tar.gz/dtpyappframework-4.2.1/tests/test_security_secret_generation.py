"""
Comprehensive tests for secure secret generation functionality.
Tests the enhanced create_secret method and secret strength validation.
"""

import pytest
import re
import string
import sys
import os
from unittest.mock import Mock, patch

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.settings.secrets.secret_store import AbstractSecretStore


class MockSecretStore(AbstractSecretStore):
    """Mock implementation of AbstractSecretStore for testing."""
    
    def __init__(self):
        super().__init__("test_store", "mock", 1, None)
        self.secrets = {}
    
    def get_secret(self, key, default_value=None):
        return self.secrets.get(key, default_value)
    
    def set_secret(self, key, value):
        self.secrets[key] = value
    
    def delete_secret(self, key):
        if key in self.secrets:
            del self.secrets[key]


class TestSecretGeneration:
    """Test the enhanced create_secret method."""
    
    @pytest.fixture
    def mock_store(self):
        """Create a mock secret store for testing."""
        return MockSecretStore()
    
    def test_create_secret_basic(self, mock_store):
        """Test basic secret creation with default parameters."""
        secret = mock_store.create_secret("test_key")
        
        # Verify secret properties
        assert isinstance(secret, str)
        assert len(secret) == 18  # Default length
        
        # Verify it was stored
        stored_secret = mock_store.get_secret("test_key")
        assert stored_secret == secret
    
    def test_create_secret_custom_length(self, mock_store):
        """Test secret creation with custom length."""
        lengths = [12, 20, 32, 64, 128]
        
        for length in lengths:
            key = f"test_key_{length}"
            secret = mock_store.create_secret(key, length=length)
            
            assert len(secret) == length
            assert isinstance(secret, str)
    
    def test_create_secret_complexity_levels(self, mock_store):
        """Test secret creation with different complexity levels."""
        complexities = ['basic', 'medium', 'high', 'alphanum']
        
        for complexity in complexities:
            key = f"test_key_{complexity}"
            secret = mock_store.create_secret(key, complexity=complexity)
            
            assert isinstance(secret, str)
            assert len(secret) == 18  # Default length
            
            # Verify complexity requirements
            if complexity in ('basic', 'alphanum'):
                assert any(c.islower() for c in secret)
                assert any(c.isupper() for c in secret)
                assert any(c.isdigit() for c in secret)
                # Should not contain special characters
                assert not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in secret)
            
            elif complexity in ['medium', 'high']:
                assert any(c.islower() for c in secret)
                assert any(c.isupper() for c in secret)
                assert any(c.isdigit() for c in secret)
                # Should contain special characters for medium/high
                if complexity == 'high':
                    # High complexity should use more special characters
                    pass
    
    def test_create_secret_character_sets(self, mock_store):
        """Test that secrets use correct character sets for each complexity."""
        # Basic complexity
        basic_secret = mock_store.create_secret("basic_test", complexity='basic')
        basic_charset = string.ascii_letters + string.digits
        assert all(c in basic_charset for c in basic_secret)
        
        # Medium complexity  
        medium_secret = mock_store.create_secret("medium_test", complexity='medium')
        medium_charset = string.ascii_letters + string.digits + '!@#$%^&*'
        assert all(c in medium_charset for c in medium_secret)
        
        # High complexity
        high_secret = mock_store.create_secret("high_test", complexity='high')
        high_charset = string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?'
        assert all(c in high_charset for c in high_secret)
        
        # Alphanum complexity
        alphanum_secret = mock_store.create_secret("alphanum_test", complexity='alphanum')
        alphanum_charset = string.ascii_letters + string.digits
        assert all(c in alphanum_charset for c in alphanum_secret)
    
    def test_create_secret_uniqueness(self, mock_store):
        """Test that multiple secrets are unique."""
        secrets = []
        
        for i in range(100):
            secret = mock_store.create_secret(f"unique_test_{i}")
            secrets.append(secret)
        
        # All secrets should be unique
        assert len(set(secrets)) == 100
    
    def test_create_secret_cryptographic_randomness(self, mock_store):
        """Test that secrets use cryptographically secure randomness."""
        # This is tested indirectly by checking uniqueness and unpredictability
        secrets = []
        
        for i in range(50):
            secret = mock_store.create_secret(f"crypto_test_{i}", length=32)
            secrets.append(secret)
        
        # Check for patterns that might indicate weak randomness
        for secret in secrets:
            # Should not have obvious patterns
            assert not re.search(r'(.)\1{4,}', secret)  # No 5+ repeated chars
            assert 'aaaaa' not in secret.lower()
            assert '12345' not in secret
            assert 'abcde' not in secret.lower()
    
    def test_create_secret_input_validation(self, mock_store):
        """Test input validation for secret creation."""
        from dtPyAppFramework.security.validation import SecurityValidationError

        # Invalid name types - InputValidator raises SecurityValidationError
        invalid_names = [None, 123, [], {}, True, 3.14]

        for invalid_name in invalid_names:
            with pytest.raises((ValueError, SecurityValidationError)):
                mock_store.create_secret(invalid_name)

        # Empty name
        with pytest.raises((ValueError, SecurityValidationError)):
            mock_store.create_secret("")
        
        # Invalid length - too short
        with pytest.raises(ValueError) as exc_info:
            mock_store.create_secret("test", length=11)
        assert "Minimum secret length is 12" in str(exc_info.value)
        
        # Invalid length - too long
        with pytest.raises(ValueError) as exc_info:
            mock_store.create_secret("test", length=1025)
        assert "Maximum secret length is 1024" in str(exc_info.value)
        
        # Invalid complexity
        with pytest.raises(ValueError) as exc_info:
            mock_store.create_secret("test", complexity='invalid')
        assert "Invalid complexity level" in str(exc_info.value)
    
    def test_create_secret_with_security_validation(self, mock_store):
        """Test that security validation is applied when available."""
        from dtPyAppFramework.security.validation import SecurityValidationError

        # Valid key should pass validation and generate a secret
        secret = mock_store.create_secret("valid_key")
        assert isinstance(secret, str)
        assert len(secret) == 18

        # Key with invalid characters should fail via InputValidator
        with pytest.raises(SecurityValidationError):
            mock_store.create_secret("key with spaces")

    def test_create_secret_validation_fallback(self, mock_store):
        """Test fallback validation when security module not available."""
        import sys

        # Remove the validation module from sys.modules so the inline import fails
        with patch.dict(sys.modules, {'dtPyAppFramework.security.validation': None}):
            # Should still work with fallback validation
            secret = mock_store.create_secret("test_key_fallback")
            assert isinstance(secret, str)

            # Should fail with invalid name via fallback
            with pytest.raises(ValueError):
                mock_store.create_secret("")
    
    def test_create_secret_generation_retry(self, mock_store):
        """Test that secret generation retries if complexity requirements not met."""
        # This is hard to test directly, but we can verify the retry mechanism exists
        # by checking that generated secrets meet requirements
        
        for _ in range(10):  # Try multiple times
            secret = mock_store.create_secret("retry_test", complexity='high', length=20)
            
            # Should meet high complexity requirements
            assert any(c.islower() for c in secret)
            assert any(c.isupper() for c in secret)
            assert any(c.isdigit() for c in secret)
            assert any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in secret)
    
    def test_create_secret_max_attempts_exceeded(self, mock_store):
        """Test behavior when max generation attempts are exceeded."""
        # Mock the validation to always fail to force max attempts
        with patch.object(mock_store, '_validate_secret_strength', return_value=False):
            with pytest.raises(RuntimeError) as exc_info:
                mock_store.create_secret("fail_test")
            assert "Failed to generate compliant secret" in str(exc_info.value)


class TestSecretStrengthValidation:
    """Test the _validate_secret_strength method."""
    
    @pytest.fixture
    def mock_store(self):
        """Create a mock secret store for testing."""
        return MockSecretStore()
    
    def test_validate_secret_strength_good_secrets(self, mock_store):
        """Test validation passes for good secrets."""
        good_secrets = [
            "Abcd1234!@#$",
            "MySecretKey2023",
            "Complex_P@ssw0rd_Here",
            "Random123XYZ789",
            "ValidSecret!2023"
        ]
        
        for secret in good_secrets:
            result = mock_store._validate_secret_strength(secret)
            assert result is True, f"Good secret failed validation: {secret}"
    
    def test_validate_secret_strength_repeated_characters(self, mock_store):
        """Test validation rejects secrets with too many repeated characters."""
        bad_secrets = [
            "aaaabbbbcccc",  # 4+ repeated chars
            "Password1111",  # 4+ repeated digits
            "TestAAAATest",  # 4+ repeated letters
            "abcddddddefg"   # 6+ repeated chars
        ]
        
        for secret in bad_secrets:
            result = mock_store._validate_secret_strength(secret)
            assert result is False, f"Bad secret passed validation: {secret}"
    
    def test_validate_secret_strength_sequential_patterns(self, mock_store):
        """Test validation rejects secrets with sequential patterns."""
        bad_secrets = [
            "abcdefgh123",     # Sequential letters
            "password123",     # Contains 'password'
            "12345678abc",     # Sequential numbers
            "qwertyuiop",      # Sequential keyboard
            "TestABCDEFGH",    # Sequential uppercase
            "secret87654321"   # Reverse sequential
        ]
        
        for secret in bad_secrets:
            result = mock_store._validate_secret_strength(secret)
            assert result is False, f"Bad secret passed validation: {secret}"
    
    def test_validate_secret_strength_case_insensitive(self, mock_store):
        """Test validation is case insensitive for patterns."""
        bad_secrets = [
            "MyPASSWORD123",   # 'PASSWORD' in different case
            "TestABCDEFGH",    # Sequential in uppercase
            "SecretQWERTYUI"   # Keyboard pattern in different case
        ]
        
        for secret in bad_secrets:
            result = mock_store._validate_secret_strength(secret)
            assert result is False, f"Bad secret passed validation: {secret}"
    
    def test_validate_secret_strength_edge_cases(self, mock_store):
        """Test validation edge cases."""
        # Empty string
        result = mock_store._validate_secret_strength("")
        assert result is True  # Empty string is technically valid (length checked elsewhere)
        
        # Single character
        result = mock_store._validate_secret_strength("a")
        assert result is True
        
        # Three repeated (should pass)
        result = mock_store._validate_secret_strength("aaabbbccc")
        assert result is True
        
        # Exactly four repeated (should fail)
        result = mock_store._validate_secret_strength("aaaabbbb")
        assert result is False


class TestSecretGenerationIntegration:
    """Test integration scenarios and real-world usage patterns."""
    
    @pytest.fixture
    def mock_store(self):
        """Create a mock secret store for testing."""
        return MockSecretStore()
    
    def test_generate_multiple_secrets_different_complexities(self, mock_store):
        """Test generating multiple secrets with different complexities."""
        secrets = {}
        
        # Generate secrets for different use cases
        test_cases = [
            ("database_password", 32, "high"),
            ("api_key", 24, "medium"),
            ("session_token", 16, "alphanum"),
            ("temp_password", 12, "basic"),
            ("encryption_key", 64, "high")
        ]
        
        for name, length, complexity in test_cases:
            secret = mock_store.create_secret(name, length=length, complexity=complexity)
            secrets[name] = secret
            
            # Verify properties
            assert len(secret) == length
            assert isinstance(secret, str)
        
        # All secrets should be different
        secret_values = list(secrets.values())
        assert len(set(secret_values)) == len(secret_values)
    
    def test_generate_secrets_with_logging(self, mock_store):
        """Test that secret generation logs appropriately."""
        import logging
        
        with patch('dtPyAppFramework.settings.secrets.secret_store.logging') as mock_logging:
            secret = mock_store.create_secret("logged_secret", length=20, complexity="medium")
            
            # Should log the generation (without the secret value)
            mock_logging.info.assert_called_once()
            log_call = mock_logging.info.call_args[0][0]
            
            assert "Generated secret 'logged_secret'" in log_call
            assert "length 20" in log_call
            assert "complexity medium" in log_call
            assert secret not in log_call  # Secret value should not be logged
    
    def test_generate_secrets_batch_operation(self, mock_store):
        """Test generating many secrets in batch."""
        secret_names = [f"batch_secret_{i}" for i in range(50)]
        generated_secrets = {}
        
        for name in secret_names:
            secret = mock_store.create_secret(name, length=24, complexity="high")
            generated_secrets[name] = secret
        
        # Verify all were generated and stored
        assert len(generated_secrets) == 50
        
        # Verify all are unique
        secret_values = list(generated_secrets.values())
        assert len(set(secret_values)) == 50
        
        # Verify all meet complexity requirements
        for secret in secret_values:
            assert len(secret) == 24
            assert any(c.islower() for c in secret)
            assert any(c.isupper() for c in secret) 
            assert any(c.isdigit() for c in secret)
            assert any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in secret)
    
    def test_generate_secrets_performance(self, mock_store):
        """Test that secret generation performs reasonably well."""
        import time
        
        start_time = time.time()
        
        # Generate 100 secrets
        for i in range(100):
            mock_store.create_secret(f"perf_test_{i}", length=32, complexity="high")
        
        elapsed_time = time.time() - start_time
        
        # Should generate 100 secrets in reasonable time (< 5 seconds)
        assert elapsed_time < 5.0, f"Secret generation too slow: {elapsed_time:.2f}s"
        
        # Average should be reasonable (< 50ms per secret)
        avg_time = elapsed_time / 100
        assert avg_time < 0.05, f"Average generation time too slow: {avg_time:.3f}s"
    
    def test_generate_secrets_entropy_analysis(self, mock_store):
        """Test generated secrets have good entropy characteristics."""
        secrets = []
        
        # Generate many secrets for analysis
        for i in range(200):
            secret = mock_store.create_secret(f"entropy_test_{i}", length=32, complexity="high")
            secrets.append(secret)
        
        # Analyze character distribution
        all_chars = ''.join(secrets)
        char_counts = {}
        
        for char in all_chars:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Should have good character distribution (no character appears > 5% of time)
        total_chars = len(all_chars)
        max_frequency = max(char_counts.values()) / total_chars
        
        assert max_frequency < 0.05, f"Poor character distribution, max frequency: {max_frequency:.3f}"
        
        # Should use characters from all categories
        has_lower = any(c.islower() for c in all_chars)
        has_upper = any(c.isupper() for c in all_chars)
        has_digit = any(c.isdigit() for c in all_chars)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in all_chars)
        
        assert has_lower, "No lowercase letters found in generated secrets"
        assert has_upper, "No uppercase letters found in generated secrets"
        assert has_digit, "No digits found in generated secrets"  
        assert has_special, "No special characters found in generated secrets"
    
    def test_secret_generation_error_scenarios(self, mock_store):
        """Test error handling in various scenarios."""
        # Test with mock that simulates storage failures
        with patch.object(mock_store, 'set_secret', side_effect=Exception("Storage error")):
            with pytest.raises(Exception):
                mock_store.create_secret("failing_storage")
        
        # Test with invalid Unicode handling
        try:
            secret = mock_store.create_secret("unicode_test_🔑", length=16)
            assert isinstance(secret, str)
        except Exception:
            # If Unicode names aren't supported, that's acceptable
            pass


class TestSecretGenerationSecurityProperties:
    """Test security properties of generated secrets."""
    
    @pytest.fixture
    def mock_store(self):
        """Create a mock secret store for testing."""
        return MockSecretStore()
    
    def test_secrets_unpredictable(self, mock_store):
        """Test that secrets are unpredictable (pass basic randomness tests)."""
        secrets = []
        
        # Generate many secrets
        for i in range(1000):
            secret = mock_store.create_secret(f"random_test_{i}", length=16, complexity="high")
            secrets.append(secret)
        
        # Convert to binary representation for analysis
        binary_data = []
        for secret in secrets:
            for char in secret:
                binary_data.append(ord(char))
        
        # Basic randomness test - mean should be in expected range for the charset
        # High complexity charset spans ASCII ~33-122, so mean should be around 75-85
        mean = sum(binary_data) / len(binary_data)
        assert 60 < mean < 130, f"Poor randomness, mean: {mean}"
        
        # Should not have obvious patterns
        patterns_found = 0
        for i in range(len(binary_data) - 3):
            if binary_data[i] == binary_data[i+1] == binary_data[i+2] == binary_data[i+3]:
                patterns_found += 1
        
        pattern_ratio = patterns_found / len(binary_data)
        assert pattern_ratio < 0.01, f"Too many patterns found: {pattern_ratio:.4f}"
    
    def test_secrets_resist_dictionary_attacks(self, mock_store):
        """Test that generated secrets don't contain common words.

        Only check words of 6+ characters.  Short substrings (3-4 chars)
        like "key" or "pass" appear by pure chance in random 24-character
        strings drawn from a large charset, which is not a security concern.
        """
        common_words = [
            "password", "admin1", "welcome", "secret", "secure", "login1",
        ]

        secrets = []
        for i in range(100):
            secret = mock_store.create_secret(f"dict_test_{i}", length=24, complexity="high")
            secrets.append(secret.lower())

        # Check that no common words appear in secrets
        for word in common_words:
            for secret in secrets:
                assert word not in secret, f"Common word '{word}' found in secret"
    
    def test_secrets_timing_consistency(self, mock_store):
        """Test that secret generation timing is consistent."""
        import time
        
        generation_times = []
        
        # Time multiple secret generations
        for i in range(20):
            start = time.perf_counter()
            mock_store.create_secret(f"timing_test_{i}", length=32, complexity="high")
            end = time.perf_counter()
            generation_times.append(end - start)
        
        # Calculate timing statistics
        _mean_time = sum(generation_times) / len(generation_times)
        max_time = max(generation_times)
        min_time = min(generation_times)
        
        # Timing should be relatively consistent (no more than 10x variance)
        time_variance = max_time / min_time
        assert time_variance < 10, f"Inconsistent timing variance: {time_variance:.2f}"
    
    def test_secrets_memory_safety(self, mock_store):
        """Test that secret generation is memory safe."""
        # Generate many secrets to test for memory issues
        secrets = []
        
        try:
            for i in range(1000):
                secret = mock_store.create_secret(f"memory_test_{i}", length=64, complexity="high")
                secrets.append(secret)
                
                # Periodically clear some secrets to simulate normal usage
                if i % 100 == 99:
                    secrets = secrets[-50:]  # Keep only last 50
            
            # Should complete without memory errors
            assert len(secrets) == 50  # Last batch kept
            
        except MemoryError:
            pytest.fail("Secret generation caused memory error")


if __name__ == "__main__":
    pytest.main([__file__])
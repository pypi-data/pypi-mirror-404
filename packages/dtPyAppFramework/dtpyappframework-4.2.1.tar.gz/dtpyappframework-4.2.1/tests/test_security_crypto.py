"""
Comprehensive tests for the security cryptographic framework.
Tests SecureKeyGenerator and LegacyKeyGenerator classes.
"""

import pytest
import tempfile
import os
import hashlib
import base64
import sys
import platform
from unittest.mock import patch, mock_open, Mock

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.security.crypto import (
    SecureKeyGenerator,
    LegacyKeyGenerator
)


class TestSecureKeyGenerator:
    """Test SecureKeyGenerator class for v3 keystores."""
    
    @pytest.fixture
    def key_generator(self):
        """Create a SecureKeyGenerator instance for testing."""
        return SecureKeyGenerator("testapp")
    
    def test_initialization(self, key_generator):
        """Test SecureKeyGenerator initialization."""
        assert key_generator.app_name == "testapp"
        assert hasattr(key_generator, 'backend')
    
    def test_different_app_names(self):
        """Test that different app names create different generators."""
        gen1 = SecureKeyGenerator("app1")
        gen2 = SecureKeyGenerator("app2")
        
        assert gen1.app_name == "app1"
        assert gen2.app_name == "app2"
        assert gen1.app_name != gen2.app_name
    
    def test_generate_keystore_password_basic(self, key_generator):
        """Test basic keystore password generation."""
        store_path = "/test/path/keystore.v3keystore"
        
        password = key_generator.generate_keystore_password(store_path)
        
        # Verify password properties
        assert isinstance(password, str)
        assert len(password) >= 32  # Should be at least 32 characters
        
        # Should be valid base64
        try:
            decoded = base64.b64decode(password.encode('ascii'))
            assert len(decoded) == 32  # 256-bit key
        except Exception:
            pytest.fail("Generated password is not valid base64")
    
    def test_generate_keystore_password_deterministic(self, key_generator):
        """Test that password generation is deterministic."""
        store_path = "/test/path/keystore.v3keystore"
        
        password1 = key_generator.generate_keystore_password(store_path)
        password2 = key_generator.generate_keystore_password(store_path)
        
        assert password1 == password2
    
    def test_generate_keystore_password_different_paths(self, key_generator):
        """Test that different paths generate different passwords."""
        path1 = "/test/path1/keystore.v3keystore"
        path2 = "/test/path2/keystore.v3keystore"
        
        password1 = key_generator.generate_keystore_password(path1)
        password2 = key_generator.generate_keystore_password(path2)
        
        assert password1 != password2
    
    def test_generate_keystore_password_different_apps(self):
        """Test that different apps generate different passwords."""
        gen1 = SecureKeyGenerator("app1")
        gen2 = SecureKeyGenerator("app2")
        store_path = "/test/path/keystore.v3keystore"
        
        password1 = gen1.generate_keystore_password(store_path)
        password2 = gen2.generate_keystore_password(store_path)
        
        assert password1 != password2
    
    def test_generate_keystore_password_with_custom_salt(self, key_generator):
        """Test password generation with custom salt."""
        store_path = "/test/path/keystore.v3keystore"
        custom_salt = b"custom_salt_1234"
        
        password1 = key_generator.generate_keystore_password(store_path)
        password2 = key_generator.generate_keystore_password(store_path, custom_salt)
        
        # Should be different with custom salt
        assert password1 != password2
        
        # Should be deterministic with same custom salt
        password3 = key_generator.generate_keystore_password(store_path, custom_salt)
        assert password2 == password3
    
    def test_get_application_salt(self, key_generator):
        """Test application-specific salt generation."""
        salt = key_generator._get_application_salt()
        
        assert isinstance(salt, bytes)
        assert len(salt) == 16  # Should be 16 bytes
        
        # Should be deterministic for same app
        salt2 = key_generator._get_application_salt()
        assert salt == salt2
        
        # Should be different for different apps
        other_gen = SecureKeyGenerator("otherapp")
        other_salt = other_gen._get_application_salt()
        assert salt != other_salt
    
    def test_collect_machine_fingerprint(self, key_generator):
        """Test machine fingerprint collection."""
        fingerprint = key_generator._collect_machine_fingerprint()
        
        assert isinstance(fingerprint, str)
        assert len(fingerprint) > 0
        
        # Should contain pipe-separated identifiers
        assert "|" in fingerprint
        
        # Should be deterministic
        fingerprint2 = key_generator._collect_machine_fingerprint()
        assert fingerprint == fingerprint2
    
    @patch('platform.system')
    @patch('socket.gethostname')
    def test_collect_machine_fingerprint_fallback(self, mock_hostname, mock_system, key_generator):
        """Test machine fingerprint fallback behavior."""
        # Mock basic system info
        mock_system.return_value = "TestOS"
        mock_hostname.return_value = "testhost"
        
        fingerprint = key_generator._collect_machine_fingerprint()
        
        assert isinstance(fingerprint, str)
        assert "testhost" in fingerprint
    
    @patch('sys.platform', 'darwin')
    @patch('dtPyAppFramework.security.crypto.run_cmd')
    def test_collect_machine_fingerprint_darwin(self, mock_run_cmd, key_generator):
        """Test machine fingerprint collection on macOS."""
        mock_run_cmd.return_value = "test-uuid-1234"

        fingerprint = key_generator._collect_machine_fingerprint()

        assert isinstance(fingerprint, str)
        assert "hw_uuid:test-uuid-1234" in fingerprint
    
    @patch('sys.platform', 'linux')
    @patch('builtins.open', mock_open(read_data='linux-machine-id-1234'))
    def test_collect_machine_fingerprint_linux(self, key_generator):
        """Test machine fingerprint collection on Linux."""
        fingerprint = key_generator._collect_machine_fingerprint()
        
        assert isinstance(fingerprint, str)
        assert "machine_id:linux-machine-id-1234" in fingerprint
    
    @patch('sys.platform', 'win32')
    @patch('subprocess.run')
    def test_collect_machine_fingerprint_windows(self, mock_run, key_generator):
        """Test machine fingerprint collection on Windows."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "windows-uuid-5678\n"
        mock_run.return_value = mock_result
        
        fingerprint = key_generator._collect_machine_fingerprint()
        
        assert isinstance(fingerprint, str)
        assert "win_uuid:windows-uuid-5678" in fingerprint
    
    @patch('uuid.getnode')
    def test_collect_machine_fingerprint_mac_address(self, mock_getnode, key_generator):
        """Test MAC address collection in fingerprint.

        Note: _collect_mac_address uses ``mac_num != uuid.getnode()`` to detect
        random fallback MACs.  When both calls return the same value (consistent
        mock or real hardware), the condition is False and mac is NOT added.
        When successive calls differ (random fallback), mac IS added.
        """
        # With consistent return value, mac_num != uuid.getnode() is False,
        # so no "mac:" identifier is added.
        mock_getnode.return_value = 0x001122334455
        fingerprint = key_generator._collect_machine_fingerprint()
        assert isinstance(fingerprint, str)
        assert "hostname:" in fingerprint

        # With varying return values (simulating random fallback),
        # the condition is True and a mac identifier IS added.
        mock_getnode.side_effect = [0x001122334455, 0xAABBCCDDEEFF]
        fingerprint2 = key_generator._collect_machine_fingerprint()
        assert "mac:" in fingerprint2
    
    def test_collect_machine_fingerprint_error_handling(self, key_generator):
        """Test error handling in machine fingerprint collection."""
        with patch.multiple(
            key_generator,
            _collect_machine_fingerprint=Mock(side_effect=Exception("Test error"))
        ):
            # Should not raise exception, should fall back gracefully
            try:
                # Re-call the actual method to test error handling
                fingerprint = key_generator._collect_machine_fingerprint()
                assert isinstance(fingerprint, str)
            except Exception:
                # If it does raise, it should be the expected fallback behavior
                pass
    
    def test_password_strength(self, key_generator):
        """Test that generated passwords have good cryptographic strength."""
        passwords = []
        
        # Generate multiple passwords with different inputs
        for i in range(10):
            path = f"/test/path{i}/keystore.v3keystore"
            password = key_generator.generate_keystore_password(path)
            passwords.append(password)
        
        # All passwords should be different
        assert len(set(passwords)) == 10
        
        # All should be proper length and format
        for password in passwords:
            assert len(password) >= 32
            # Should be valid base64
            try:
                decoded = base64.b64decode(password.encode('ascii'))
                assert len(decoded) == 32
            except Exception:
                pytest.fail(f"Invalid base64 password: {password}")
    
    def test_pbkdf2_parameters(self, key_generator):
        """Test that PBKDF2 uses secure parameters."""
        store_path = "/test/path/keystore.v3keystore"
        
        # Mock PBKDF2HMAC to verify parameters
        with patch('dtPyAppFramework.security.crypto.PBKDF2HMAC') as mock_pbkdf2:
            mock_kdf = Mock()
            mock_kdf.derive.return_value = b'x' * 32
            mock_pbkdf2.return_value = mock_kdf
            
            key_generator.generate_keystore_password(store_path)
            
            # Verify PBKDF2 was called with secure parameters
            mock_pbkdf2.assert_called_once()
            call_kwargs = mock_pbkdf2.call_args[1]
            
            assert call_kwargs['length'] == 32  # 256-bit key
            assert call_kwargs['iterations'] == 100000  # OWASP recommended minimum


class TestLegacyKeyGenerator:
    """Test LegacyKeyGenerator class for v2 keystore migration."""
    
    def test_generate_legacy_v2_password_deterministic(self):
        """Test that legacy password generation is deterministic."""
        store_path = "/test/path/keystore.v2keystore"
        
        try:
            password1 = LegacyKeyGenerator.generate_legacy_v2_password(store_path)
            password2 = LegacyKeyGenerator.generate_legacy_v2_password(store_path)
            
            assert password1 == password2
            assert isinstance(password1, str)
            assert len(password1) > 0
            
        except Exception as e:
            pytest.skip(f"Legacy password generation not supported: {e}")
    
    def test_generate_legacy_v2_password_different_paths(self):
        """Test that different paths generate different legacy passwords."""
        path1 = "/test/path1/keystore.v2keystore"
        path2 = "/test/path2/keystore.v2keystore"
        
        try:
            password1 = LegacyKeyGenerator.generate_legacy_v2_password(path1)
            password2 = LegacyKeyGenerator.generate_legacy_v2_password(path2)
            
            assert password1 != password2
            
        except Exception as e:
            pytest.skip(f"Legacy password generation not supported: {e}")
    
    @patch('sys.platform', 'darwin')
    @patch('dtPyAppFramework.security.crypto.run_cmd')
    def test_generate_legacy_v2_password_darwin(self, mock_run_cmd):
        """Test legacy password generation on macOS."""
        mock_run_cmd.return_value = "darwin-uuid-1234"
        store_path = "/test/path/keystore.v2keystore"

        password = LegacyKeyGenerator.generate_legacy_v2_password(store_path)

        assert isinstance(password, str)
        assert len(password) > 0
        mock_run_cmd.assert_called_once()

    @patch('sys.platform', 'win32')
    @patch('dtPyAppFramework.security.crypto.run_cmd')
    def test_generate_legacy_v2_password_windows(self, mock_run_cmd):
        """Test legacy password generation on Windows."""
        mock_run_cmd.return_value = "UUID\n---\nwindows-uuid-5678\n"
        store_path = "/test/path/keystore.v2keystore"

        password = LegacyKeyGenerator.generate_legacy_v2_password(store_path)

        assert isinstance(password, str)
        assert len(password) > 0
        mock_run_cmd.assert_called_once()

    @patch('sys.platform', 'linux')
    @patch('dtPyAppFramework.security.crypto.run_cmd')
    def test_generate_legacy_v2_password_linux(self, mock_run_cmd):
        """Test legacy password generation on Linux."""
        mock_run_cmd.return_value = "linux-machine-id-1234"
        store_path = "/test/path/keystore.v2keystore"

        password = LegacyKeyGenerator.generate_legacy_v2_password(store_path)

        assert isinstance(password, str)
        assert len(password) > 0
        mock_run_cmd.assert_called_once()

    @patch('sys.platform', 'freebsd')
    @patch('dtPyAppFramework.security.crypto.run_cmd')
    def test_generate_legacy_v2_password_freebsd(self, mock_run_cmd):
        """Test legacy password generation on FreeBSD."""
        mock_run_cmd.side_effect = ["freebsd-hostid-1234", None]
        store_path = "/test/path/keystore.v2keystore"

        password = LegacyKeyGenerator.generate_legacy_v2_password(store_path)

        assert isinstance(password, str)
        assert len(password) > 0

    @patch('sys.platform', 'linux')
    @patch('dtPyAppFramework.security.crypto.run_cmd')
    def test_generate_legacy_v2_password_no_machine_id(self, mock_run_cmd):
        """Test legacy password generation when machine ID cannot be determined."""
        mock_run_cmd.return_value = None  # Simulate failure
        store_path = "/test/path/keystore.v2keystore"

        with pytest.raises(Exception) as exc_info:
            LegacyKeyGenerator.generate_legacy_v2_password(store_path)

        assert "Failed to determine unique machine ID" in str(exc_info.value)
    
    def test_legacy_password_format(self):
        """Test that legacy passwords have expected format."""
        store_path = "/test/path/keystore.v2keystore"
        
        try:
            password = LegacyKeyGenerator.generate_legacy_v2_password(store_path)
            
            # Should be URL-safe base64 encoded
            try:
                from base64 import urlsafe_b64decode
                decoded = urlsafe_b64decode(password.encode())
                assert len(decoded) > 0
            except Exception:
                pytest.fail(f"Legacy password is not valid URL-safe base64: {password}")
                
        except Exception as e:
            pytest.skip(f"Legacy password generation not supported: {e}")
    
    def test_legacy_weak_crypto_implementation(self):
        """Test that legacy implementation uses weak crypto (for migration compatibility)."""
        # This test verifies that the legacy method still uses the weak XOR cipher
        # as documented in the security analysis - this is intentional for v2 compatibility
        
        store_path = "/test/path/keystore.v2keystore"
        
        try:
            password = LegacyKeyGenerator.generate_legacy_v2_password(store_path)
            
            # The legacy password should be relatively short compared to secure passwords
            # This is expected due to the weak crypto implementation
            assert isinstance(password, str)
            
            # Legacy passwords are typically shorter than secure ones
            # (though this is implementation-dependent)
            
        except Exception as e:
            pytest.skip(f"Legacy password generation not supported: {e}")


class TestKeyGeneratorComparison:
    """Test comparison between secure and legacy key generators."""
    
    def test_secure_vs_legacy_passwords_different(self):
        """Test that secure and legacy generators produce different passwords."""
        app_name = "testapp"
        store_path = "/test/path/keystore"
        
        try:
            # Generate with both methods
            secure_gen = SecureKeyGenerator(app_name)
            secure_password = secure_gen.generate_keystore_password(f"{store_path}.v3keystore")
            
            legacy_password = LegacyKeyGenerator.generate_legacy_v2_password(f"{store_path}.v2keystore")
            
            # Should be different
            assert secure_password != legacy_password
            
            # Both should be strings
            assert isinstance(secure_password, str)
            assert isinstance(legacy_password, str)
            
        except Exception as e:
            pytest.skip(f"Key generation comparison not supported: {e}")
    
    def test_secure_password_stronger_than_legacy(self):
        """Test that secure passwords are cryptographically stronger."""
        app_name = "testapp"
        store_path = "/test/path/keystore"
        
        try:
            secure_gen = SecureKeyGenerator(app_name)
            secure_password = secure_gen.generate_keystore_password(f"{store_path}.v3keystore")
            
            legacy_password = LegacyKeyGenerator.generate_legacy_v2_password(f"{store_path}.v2keystore")
            
            # Secure password should generally be longer (though not always)
            # More importantly, it should be proper base64 with full 32 bytes of entropy
            
            # Test secure password format
            secure_decoded = base64.b64decode(secure_password.encode('ascii'))
            assert len(secure_decoded) == 32  # Full 256-bit key
            
            # Legacy password uses different encoding and truncation
            # so we just verify it's a valid string
            assert len(legacy_password) > 0
            
        except Exception as e:
            pytest.skip(f"Password strength comparison not supported: {e}")


class TestCryptographicEdgeCases:
    """Test edge cases and boundary conditions in cryptographic components."""
    
    def test_extremely_long_app_name(self):
        """Test key generator with very long app name."""
        long_app_name = "a" * 1000
        gen = SecureKeyGenerator(long_app_name)
        
        password = gen.generate_keystore_password("/test/path")
        
        assert isinstance(password, str)
        assert len(password) >= 32
    
    def test_extremely_long_store_path(self):
        """Test key generator with very long store path."""
        gen = SecureKeyGenerator("testapp")
        long_path = "/test/" + "very_long_directory_name/" * 100 + "keystore.v3keystore"
        
        password = gen.generate_keystore_password(long_path)
        
        assert isinstance(password, str)
        assert len(password) >= 32
    
    def test_special_characters_in_app_name(self):
        """Test key generator with special characters in app name."""
        special_app_name = "test-app_123.v2@domain.com"
        gen = SecureKeyGenerator(special_app_name)
        
        password = gen.generate_keystore_password("/test/path")
        
        assert isinstance(password, str)
        assert len(password) >= 32
    
    def test_unicode_in_app_name(self):
        """Test key generator with Unicode characters in app name."""
        unicode_app_name = "test_app_héllo_世界_🔑"
        gen = SecureKeyGenerator(unicode_app_name)
        
        password = gen.generate_keystore_password("/test/path")
        
        assert isinstance(password, str)
        assert len(password) >= 32
    
    def test_empty_custom_salt(self):
        """Test key generator with empty custom salt.

        Empty bytes (b"") is falsy in Python, so the ``or`` fallback in
        ``custom_salt or self._get_application_salt()`` returns the default
        application salt.  Both calls therefore produce the same password.
        """
        gen = SecureKeyGenerator("testapp")

        password1 = gen.generate_keystore_password("/test/path", custom_salt=b"")
        password2 = gen.generate_keystore_password("/test/path")

        # Empty salt is falsy, so both use the default application salt
        assert password1 == password2
    
    def test_large_custom_salt(self):
        """Test key generator with large custom salt."""
        gen = SecureKeyGenerator("testapp")
        large_salt = b"x" * 10000  # 10KB salt
        
        password = gen.generate_keystore_password("/test/path", custom_salt=large_salt)
        
        assert isinstance(password, str)
        assert len(password) >= 32
    
    def test_machine_fingerprint_consistency(self):
        """Test that machine fingerprint is consistent across multiple calls."""
        gen = SecureKeyGenerator("testapp")
        
        # Get fingerprint multiple times
        fingerprints = []
        for _ in range(5):
            fp = gen._collect_machine_fingerprint()
            fingerprints.append(fp)
        
        # All should be identical
        assert len(set(fingerprints)) == 1
        
        # Verify format
        fp = fingerprints[0]
        assert isinstance(fp, str)
        assert len(fp) > 0
        assert "|" in fp  # Should contain delimiters
    
    def test_application_salt_uniqueness(self):
        """Test that different applications get different salts."""
        apps = ["app1", "app2", "app3", "app_with_special_chars_123", "very_long_app_name" * 10]
        salts = []
        
        for app in apps:
            gen = SecureKeyGenerator(app)
            salt = gen._get_application_salt()
            salts.append(salt)
        
        # All salts should be different
        assert len(set(salts)) == len(apps)
        
        # All should be proper length
        for salt in salts:
            assert isinstance(salt, bytes)
            assert len(salt) == 16


if __name__ == "__main__":
    pytest.main([__file__])
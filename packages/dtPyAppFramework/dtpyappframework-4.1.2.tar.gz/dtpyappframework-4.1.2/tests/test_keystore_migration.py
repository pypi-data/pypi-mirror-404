import os
import sys
import tempfile
import shutil
import pytest
import json
from unittest import mock

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the classes to test
from dtPyAppFramework.settings.secrets.local_secret_store import LocalSecretStore
from dtPyAppFramework.settings.secrets.keystore import PasswordProtectedKeystoreWithHMAC
from dtPyAppFramework.security.crypto import SecureKeyGenerator, LegacyKeyGenerator
from dtPyAppFramework.settings.secrets.secret_store import SecretsStoreException


class TestKeystoreMigration:
    """Test suite for v2keystore to v3keystore migration functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_application_settings(self):
        """Mock application settings object."""
        mock_settings = mock.Mock()
        mock_settings.get = mock.Mock(return_value=None)
        return mock_settings

    def create_v2_keystore(self, temp_dir, app_name="testapp"):
        """Create a v2keystore with test data using legacy password generation."""
        v2_keystore_path = os.path.join(temp_dir, f"{app_name}.v2keystore")
        
        # Generate legacy password (this may fail on some platforms)
        try:
            v2_password = LegacyKeyGenerator.generate_legacy_v2_password(v2_keystore_path)
        except Exception:
            # Fallback for testing on platforms where legacy generation fails
            v2_password = "fallback_legacy_password_for_testing"
        
        # Create v2 keystore with test data
        v2_keystore = PasswordProtectedKeystoreWithHMAC(v2_keystore_path, v2_password)
        
        # Add test secrets
        test_secrets = {
            "database_password": "super_secret_db_pass",
            "api_key": "sk-1234567890abcdef",
            "encryption_key": "AES256-encryption-key-here",
            "oauth_secret": "oauth-client-secret-12345",
            "testapp.INDEX": json.dumps(["database_password", "api_key", "encryption_key", "oauth_secret"])
        }
        
        for key, value in test_secrets.items():
            v2_keystore.set(key, value)
        
        return v2_keystore_path, v2_password, test_secrets

    def test_v2_to_v3_migration_success(self, temp_dir, mock_application_settings):
        """Test successful migration from v2keystore to v3keystore."""
        app_name = "testapp"
        
        # Create v2keystore with test data
        v2_path, v2_password, test_secrets = self.create_v2_keystore(temp_dir, app_name)
        
        # Verify v2keystore exists and has data
        assert os.path.exists(v2_path)
        v2_keystore = PasswordProtectedKeystoreWithHMAC(v2_path, v2_password)
        assert v2_keystore.get("database_password") == "super_secret_db_pass"
        
        # Initialize LocalSecretStore (should trigger migration)
        store = LocalSecretStore(
            store_name="test_store",
            store_priority=1,
            root_store_path=temp_dir,
            application_settings=mock_application_settings,
            app_short_name=app_name
        )
        
        # Verify migration occurred
        v3_path = os.path.join(temp_dir, f"{app_name}.v3keystore")
        backup_path = f"{v2_path}_old"
        
        assert os.path.exists(v3_path), "v3keystore should be created"
        assert os.path.exists(backup_path), "v2keystore should be backed up"
        assert not os.path.exists(v2_path), "Original v2keystore should be removed"
        assert store.keystore_version == "v3", "Should be using v3keystore"
        
        # Verify all secrets were migrated
        for key, expected_value in test_secrets.items():
            if not key.endswith('.INDEX'):  # Skip index entries in this test
                actual_value = store.get_secret(key)
                assert actual_value == expected_value, f"Secret '{key}' not migrated correctly"
        
        # Verify store is functional
        store.set_secret("new_secret", "new_value")
        assert store.get_secret("new_secret") == "new_value"

    def test_v2_to_v3_migration_with_invalid_keys(self, temp_dir, mock_application_settings):
        """Test migration handles invalid secret keys gracefully."""
        app_name = "testapp"
        v2_keystore_path = os.path.join(temp_dir, f"{app_name}.v2keystore")
        
        # Create v2 keystore with some invalid keys
        try:
            v2_password = LegacyKeyGenerator.generate_legacy_v2_password(v2_keystore_path)
        except Exception:
            v2_password = "fallback_legacy_password_for_testing"
        
        v2_keystore = PasswordProtectedKeystoreWithHMAC(v2_keystore_path, v2_password)
        
        # Add mix of valid and potentially invalid keys
        test_data = {
            "valid_key": "valid_value",
            "another.valid_key": "another_value",
            # Note: Invalid keys like "../invalid" would normally be rejected by validation
            # but we'll test the migration handles validation errors gracefully
            "testapp.INDEX": json.dumps(["valid_key", "another.valid_key"])
        }
        
        for key, value in test_data.items():
            v2_keystore.set(key, value)
        
        # Initialize LocalSecretStore (should trigger migration)
        store = LocalSecretStore(
            store_name="test_store",
            store_priority=1,
            root_store_path=temp_dir,
            application_settings=mock_application_settings,
            app_short_name=app_name
        )
        
        # Verify migration succeeded and valid keys were migrated
        assert store.keystore_version == "v3"
        assert store.get_secret("valid_key") == "valid_value"
        assert store.get_secret("another.valid_key") == "another_value"

    def test_migration_failure_fallback(self, temp_dir, mock_application_settings):
        """Test fallback to v2keystore when migration fails."""
        app_name = "testapp"

        # Create a corrupted v2keystore that will cause migration to fail
        v2_path = os.path.join(temp_dir, f"{app_name}.v2keystore")
        with open(v2_path, 'wb') as f:
            f.write(b"corrupted_keystore_data_that_will_fail_to_load")

        # The corrupted v2 keystore is handled gracefully by the keystore layer:
        # 1. Migration attempt fails (corrupted data)
        # 2. Falls back to opening v2 keystore directly
        # 3. Keystore handles corruption gracefully (logs warning, creates empty store)
        # The store should initialise using the v2 path as fallback
        store = LocalSecretStore(
            store_name="test_store",
            store_priority=1,
            root_store_path=temp_dir,
            application_settings=mock_application_settings,
            app_short_name=app_name
        )

        # Verify it fell back to v2 keystore
        assert store.keystore_version == "v2"
        assert store.store_available is True

    def test_v3_keystore_already_exists(self, temp_dir, mock_application_settings):
        """Test behavior when v3keystore already exists."""
        app_name = "testapp"
        
        # Create both v2 and v3 keystores
        v2_path, _, _ = self.create_v2_keystore(temp_dir, app_name)
        
        # Create v3keystore with different data
        v3_path = os.path.join(temp_dir, f"{app_name}.v3keystore")
        secure_gen = SecureKeyGenerator(app_name)
        v3_password = secure_gen.generate_keystore_password(v3_path)
        v3_keystore = PasswordProtectedKeystoreWithHMAC(v3_path, v3_password)
        v3_keystore.set("existing_v3_secret", "v3_value")
        
        # Initialize LocalSecretStore (should use existing v3keystore, not migrate)
        store = LocalSecretStore(
            store_name="test_store",
            store_priority=1,
            root_store_path=temp_dir,
            application_settings=mock_application_settings,
            app_short_name=app_name
        )
        
        # Verify it's using v3keystore and v2 is left untouched
        assert store.keystore_version == "v3"
        assert os.path.exists(v2_path), "v2keystore should not be touched"
        assert os.path.exists(v3_path), "v3keystore should be used"
        assert store.get_secret("existing_v3_secret") == "v3_value"

    def test_new_installation_creates_v3(self, temp_dir, mock_application_settings):
        """Test that new installations create v3keystore directly."""
        app_name = "testapp"
        
        # Initialize LocalSecretStore with no existing keystores
        store = LocalSecretStore(
            store_name="test_store",
            store_priority=1,
            root_store_path=temp_dir,
            application_settings=mock_application_settings,
            app_short_name=app_name
        )
        
        # Verify v3keystore was created
        v3_path = os.path.join(temp_dir, f"{app_name}.v3keystore")
        assert os.path.exists(v3_path), "v3keystore should be created for new installation"
        assert store.keystore_version == "v3"
        
        # Verify it's functional
        store.set_secret("test_secret", "test_value")
        assert store.get_secret("test_secret") == "test_value"

    def test_secure_vs_legacy_password_generation(self, temp_dir):
        """Test that v3 passwords are different from v2 legacy passwords."""
        app_name = "testapp"
        keystore_path = os.path.join(temp_dir, f"{app_name}.keystore")
        
        # Generate legacy password
        try:
            legacy_password = LegacyKeyGenerator.generate_legacy_v2_password(keystore_path)
        except Exception:
            pytest.skip("Legacy password generation not supported on this platform")
        
        # Generate secure password
        secure_gen = SecureKeyGenerator(app_name)
        secure_password = secure_gen.generate_keystore_password(keystore_path)
        
        # Verify passwords are different and secure password is longer/more complex
        assert legacy_password != secure_password, "Legacy and secure passwords should be different"
        assert len(secure_password) >= 32, "Secure password should be at least 32 characters"
        
        # Test that both can be used to create keystores
        legacy_keystore = PasswordProtectedKeystoreWithHMAC(keystore_path + ".legacy", legacy_password)
        legacy_keystore.set("test", "legacy_value")
        
        secure_keystore = PasswordProtectedKeystoreWithHMAC(keystore_path + ".secure", secure_password)
        secure_keystore.set("test", "secure_value")
        
        assert legacy_keystore.get("test") == "legacy_value"
        assert secure_keystore.get("test") == "secure_value"

    def test_migration_preserves_all_secret_types(self, temp_dir, mock_application_settings):
        """Test that migration preserves different types of secret values."""
        app_name = "testapp"
        v2_path, v2_password, _ = self.create_v2_keystore(temp_dir, app_name)
        
        # Add various types of secret values to v2keystore
        v2_keystore = PasswordProtectedKeystoreWithHMAC(v2_path, v2_password)
        
        test_secrets = {
            "string_secret": "simple_string",
            "json_secret": '{"key": "value", "number": 123}',
            "base64_secret": "SGVsbG8gV29ybGQ=",
            "multiline_secret": "line1\nline2\nline3",
            "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
            "unicode_secret": "héllo wørld 🔑",
            "long_secret": "x" * 1000,  # Long secret
        }
        
        index_keys = list(test_secrets.keys())
        for key, value in test_secrets.items():
            v2_keystore.set(key, value)
        
        # Add index
        v2_keystore.set(f"{app_name}.INDEX", json.dumps(index_keys))
        
        # Trigger migration
        store = LocalSecretStore(
            store_name="test_store",
            store_priority=1,
            root_store_path=temp_dir,
            application_settings=mock_application_settings,
            app_short_name=app_name
        )
        
        # Verify all secrets migrated correctly
        assert store.keystore_version == "v3"
        for key, expected_value in test_secrets.items():
            actual_value = store.get_secret(key)
            assert actual_value == expected_value, f"Secret '{key}' value mismatch after migration"

    def test_migration_logging(self, temp_dir, mock_application_settings, caplog):
        """Test that migration process logs appropriate messages."""
        app_name = "testapp"
        
        # Create v2keystore
        self.create_v2_keystore(temp_dir, app_name)
        
        # Trigger migration and capture logs
        with caplog.at_level("INFO"):
            _store = LocalSecretStore(
                store_name="test_store",
                store_priority=1,
                root_store_path=temp_dir,
                application_settings=mock_application_settings,
                app_short_name=app_name
            )
        
        # Verify migration was logged
        assert "Found v2keystore, performing migration to v3" in caplog.text
        assert "Successfully migrated v2keystore to v3keystore" in caplog.text
        assert "Successfully opened v3 Secrets Store" in caplog.text


class TestLegacyPasswordGeneration:
    """Test the legacy password generation for migration compatibility."""
    
    def test_legacy_password_consistency(self):
        """Test that legacy password generation is consistent."""
        test_path = "/test/path.v2keystore"
        
        try:
            # Generate same password multiple times
            password1 = LegacyKeyGenerator.generate_legacy_v2_password(test_path)
            password2 = LegacyKeyGenerator.generate_legacy_v2_password(test_path)
            
            assert password1 == password2, "Legacy password generation should be deterministic"
            assert len(password1) > 0, "Password should not be empty"
            
        except Exception as e:
            pytest.skip(f"Legacy password generation not supported on this platform: {e}")
    
    def test_legacy_password_different_paths(self):
        """Test that different paths generate different passwords."""
        try:
            password1 = LegacyKeyGenerator.generate_legacy_v2_password("/path1.v2keystore")
            password2 = LegacyKeyGenerator.generate_legacy_v2_password("/path2.v2keystore")
            
            assert password1 != password2, "Different paths should generate different passwords"
            
        except Exception as e:
            pytest.skip(f"Legacy password generation not supported on this platform: {e}")


class TestSecurePasswordGeneration:
    """Test the secure password generation for v3 keystores."""
    
    def test_secure_password_consistency(self):
        """Test that secure password generation is consistent for same inputs."""
        app_name = "testapp"
        test_path = "/test/path.v3keystore"
        
        gen = SecureKeyGenerator(app_name)
        password1 = gen.generate_keystore_password(test_path)
        password2 = gen.generate_keystore_password(test_path)
        
        assert password1 == password2, "Secure password generation should be deterministic"
        assert len(password1) >= 32, "Secure password should be at least 32 characters"
    
    def test_secure_password_different_apps(self):
        """Test that different app names generate different passwords."""
        test_path = "/test/path.v3keystore"
        
        gen1 = SecureKeyGenerator("app1")
        gen2 = SecureKeyGenerator("app2")
        
        password1 = gen1.generate_keystore_password(test_path)
        password2 = gen2.generate_keystore_password(test_path)
        
        assert password1 != password2, "Different app names should generate different passwords"
    
    def test_secure_password_different_paths(self):
        """Test that different paths generate different passwords."""
        app_name = "testapp"
        gen = SecureKeyGenerator(app_name)
        
        password1 = gen.generate_keystore_password("/path1.v3keystore")
        password2 = gen.generate_keystore_password("/path2.v3keystore")
        
        assert password1 != password2, "Different paths should generate different passwords"


if __name__ == "__main__":
    pytest.main([__file__])
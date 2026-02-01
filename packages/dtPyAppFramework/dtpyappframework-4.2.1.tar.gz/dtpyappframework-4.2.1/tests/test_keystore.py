import base64
import json
import os
import sys
import tempfile
from unittest import mock

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the class to test
from dtPyAppFramework.settings.secrets.keystore import PasswordProtectedKeystoreWithHMAC

@pytest.fixture
def temp_keystore_path():
    """Create a temporary file path for keystore testing."""
    fd, temp_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)  # Close the file descriptor
    os.unlink(temp_path)  # Remove the file so keystore can create it
    yield temp_path
    # Cleanup after test
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def keystore(temp_keystore_path):
    return PasswordProtectedKeystoreWithHMAC(temp_keystore_path, 'test_password')


def test_init(keystore, temp_keystore_path):
    assert keystore.keystore_path == temp_keystore_path
    assert keystore.password == 'test_password'.encode()


def test_derive_key(keystore):
    salt = os.urandom(16)
    key = keystore._derive_key(salt)
    assert (isinstance(key, bytes))
    assert (len(key) == 44)  # Length of base64 encoded 256-bit key


def test_generate_hmac(keystore):
    salt = os.urandom(16)
    key = keystore._derive_key(salt)
    data = os.urandom(16)
    hmac = keystore._generate_hmac(data, key)
    assert (isinstance(hmac, bytes))
    assert (len(hmac) == 32)  # Length of SHA256 hash


def test_verify_hmac(keystore):
    salt = os.urandom(16)
    key = keystore._derive_key(salt)
    data = os.urandom(16)
    hmac = keystore._generate_hmac(data, key)
    assert keystore._verify_hmac(data, key, hmac) is True


def test_save_and_load_keystore(keystore):
    test_data = {"test_key": "test_value"}
    keystore._save_keystore(test_data)
    loaded_data = keystore._load_keystore()

    assert loaded_data == test_data


def test_set_get_delete_methods(keystore):
    keystore.set("test_key", "test_value")
    assert keystore.get("test_key") == "test_value"
    keystore.delete("test_key")
    assert keystore.get("test_key") is None

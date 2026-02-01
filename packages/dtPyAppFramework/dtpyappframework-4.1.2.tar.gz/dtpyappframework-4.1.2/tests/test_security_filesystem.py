"""
Comprehensive tests for the security filesystem framework.
Tests SecureFileManager class and file system security operations.
"""

import pytest
import tempfile
import os
import stat
import shutil
import hashlib
from pathlib import Path
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.security.filesystem import (
    SecureFileManager,
    FileSystemSecurityError
)


class TestFileSystemSecurityError:
    """Test FileSystemSecurityError exception class."""
    
    def test_basic_exception(self):
        """Test basic exception creation."""
        error = FileSystemSecurityError("Test message")
        assert str(error) == "Test message"
    
    def test_exception_inheritance(self):
        """Test exception inheritance."""
        error = FileSystemSecurityError("Test message")
        assert isinstance(error, Exception)


class TestSecureFileManagerValidation:
    """Test SecureFileManager validation methods."""
    
    def test_validate_file_permissions_nonexistent_file(self):
        """Test validation returns False for non-existent files."""
        result = SecureFileManager.validate_file_permissions("/nonexistent/file.txt")
        assert result is False
    
    def test_validate_file_permissions_secure_file(self):
        """Test validation passes for securely permissioned files."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        try:
            # Set secure permissions (owner read/write only)
            os.chmod(temp_path, 0o600)
            
            # Should pass validation
            result = SecureFileManager.validate_file_permissions(temp_path)
            assert result is True
            
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.skipif(os.name == 'nt', reason="Unix permissions not applicable on Windows")
    def test_validate_file_permissions_insecure_file(self):
        """Test validation fails for insecurely permissioned files."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        try:
            # Set insecure permissions (world readable)
            os.chmod(temp_path, 0o644)
            
            # Should fail validation
            with pytest.raises(FileSystemSecurityError) as exc_info:
                SecureFileManager.validate_file_permissions(temp_path)
            assert "too permissive" in str(exc_info.value)
            
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.skipif(os.name == 'nt', reason="Unix ownership not applicable on Windows")
    def test_validate_file_permissions_wrong_owner(self):
        """Test validation considers file ownership."""
        # This test is complex to implement safely as it requires
        # creating files with different owners
        pass
    
    def test_validate_file_size_valid(self):
        """Test file size validation for valid files."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"test content" * 100  # ~1.2KB
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Should pass - file is smaller than limit
            result = SecureFileManager.validate_file_size(temp_path, max_size=2048)
            assert result is True
            
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_size_too_large(self):
        """Test file size validation for oversized files."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"x" * 1000
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Should fail - file is larger than limit
            with pytest.raises(FileSystemSecurityError) as exc_info:
                SecureFileManager.validate_file_size(temp_path, max_size=500)
            assert "too large" in str(exc_info.value)
            assert "1000 bytes" in str(exc_info.value)
            assert "max: 500" in str(exc_info.value)
            
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_size_nonexistent(self):
        """Test file size validation for non-existent files."""
        result = SecureFileManager.validate_file_size("/nonexistent/file.txt", max_size=1024)
        assert result is False


class TestSecureFileManagerCreation:
    """Test SecureFileManager secure file creation methods."""
    
    def test_create_secure_file_basic(self):
        """Test basic secure file creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test_file.txt")
            content = b"test content for secure file"
            
            result_path = SecureFileManager.create_secure_file(file_path, content)
            
            # Verify file was created
            assert os.path.exists(result_path)
            # Use Path to normalize paths for comparison (handles Windows short names)
            assert Path(result_path).resolve() == Path(file_path).resolve()
            
            # Verify content
            with open(result_path, 'rb') as f:
                read_content = f.read()
            assert read_content == content
            
            # Verify permissions (Unix only)
            if os.name != 'nt':
                file_stat = os.stat(result_path)
                permissions = file_stat.st_mode & 0o777
                assert permissions == 0o600
    
    def test_create_secure_file_custom_permissions(self):
        """Test secure file creation with custom permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test_file.txt")
            content = b"test content"
            custom_permissions = 0o640
            
            result_path = SecureFileManager.create_secure_file(
                file_path, content, permissions=custom_permissions
            )
            
            # Verify file was created
            assert os.path.exists(result_path)
            
            # Verify permissions (Unix only)
            if os.name != 'nt':
                file_stat = os.stat(result_path)
                permissions = file_stat.st_mode & 0o777
                assert permissions == custom_permissions
    
    def test_create_secure_file_nested_directory(self):
        """Test secure file creation with nested directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "sub1", "sub2", "test_file.txt")
            content = b"nested file content"
            
            result_path = SecureFileManager.create_secure_file(nested_path, content)
            
            # Verify file and directories were created
            assert os.path.exists(result_path)
            assert os.path.exists(os.path.dirname(result_path))
            
            # Verify content
            with open(result_path, 'rb') as f:
                read_content = f.read()
            assert read_content == content
    
    def test_create_secure_file_atomic_operation(self):
        """Test that file creation is atomic (uses temporary file)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "atomic_test.txt")
            content = b"atomic content"
            
            # Monitor directory for temporary files during creation
            original_files = set(os.listdir(temp_dir))
            
            result_path = SecureFileManager.create_secure_file(file_path, content)
            
            final_files = set(os.listdir(temp_dir))
            
            # Should only have the final file, no temporary files left
            assert len(final_files) == len(original_files) + 1
            assert os.path.basename(result_path) in final_files
    
    def test_create_secure_file_failure_cleanup(self):
        """Test that temporary files are cleaned up on failure."""
        # Create a scenario where file creation fails
        with tempfile.TemporaryDirectory() as temp_dir:
            # Try to create file in a read-only directory
            readonly_dir = os.path.join(temp_dir, "readonly")
            os.makedirs(readonly_dir)
            
            if os.name != 'nt':  # Unix permissions
                os.chmod(readonly_dir, 0o444)  # Read-only
                
                file_path = os.path.join(readonly_dir, "should_fail.txt")
                content = b"this should fail"
                
                try:
                    with pytest.raises(FileSystemSecurityError):
                        SecureFileManager.create_secure_file(file_path, content)
                    
                    # Verify no temporary files left in directory
                    remaining_files = os.listdir(readonly_dir)
                    assert len(remaining_files) == 0
                    
                finally:
                    # Restore permissions for cleanup
                    os.chmod(readonly_dir, 0o755)
    
    def test_create_secure_file_large_content(self):
        """Test secure file creation with large content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "large_file.txt")
            # Create 1MB of content
            large_content = b"x" * (1024 * 1024)
            
            result_path = SecureFileManager.create_secure_file(file_path, large_content)
            
            # Verify file was created correctly
            assert os.path.exists(result_path)
            
            # Verify size
            file_size = os.path.getsize(result_path)
            assert file_size == len(large_content)
            
            # Verify content integrity
            with open(result_path, 'rb') as f:
                read_content = f.read()
            assert read_content == large_content


class TestSecureFileManagerDeletion:
    """Test SecureFileManager secure deletion methods."""
    
    def test_secure_delete_nonexistent_file(self):
        """Test secure deletion of non-existent file."""
        result = SecureFileManager.secure_delete("/nonexistent/file.txt")
        assert result is True  # Should return True for non-existent files
    
    def test_secure_delete_basic(self):
        """Test basic secure file deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            file_path = os.path.join(temp_dir, "delete_test.txt")
            content = b"sensitive content to be securely deleted" * 100
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Verify file exists
            assert os.path.exists(file_path)
            
            # Securely delete
            result = SecureFileManager.secure_delete(file_path)
            
            # Verify deletion
            assert result is True
            assert not os.path.exists(file_path)
    
    def test_secure_delete_multiple_passes(self):
        """Test secure deletion with multiple overwrite passes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "multipass_delete.txt")
            content = b"multi-pass deletion test content"
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Delete with 5 passes
            result = SecureFileManager.secure_delete(file_path, passes=5)
            
            assert result is True
            assert not os.path.exists(file_path)
    
    def test_secure_delete_large_file(self):
        """Test secure deletion of large files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "large_delete.txt")
            # Create 1MB file
            large_content = b"L" * (1024 * 1024)
            
            with open(file_path, 'wb') as f:
                f.write(large_content)
            
            result = SecureFileManager.secure_delete(file_path)
            
            assert result is True
            assert not os.path.exists(file_path)
    
    def test_secure_delete_permission_error(self):
        """Test secure deletion handles permission errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "permission_test.txt")
            
            with open(file_path, 'wb') as f:
                f.write(b"test content")
            
            if os.name != 'nt':  # Unix permissions
                # Make file read-only to simulate permission error
                os.chmod(file_path, 0o444)
                
                try:
                    result = SecureFileManager.secure_delete(file_path)
                    # Should return False due to permission error
                    assert result is False
                    
                finally:
                    # Restore permissions for cleanup
                    try:
                        os.chmod(file_path, 0o644)
                        os.unlink(file_path)
                    except OSError:
                        pass  # Intentionally empty test fixture
    
    def test_secure_delete_zero_size_file(self):
        """Test secure deletion of zero-size files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "empty_file.txt")
            
            # Create empty file
            Path(file_path).touch()

            result = SecureFileManager.secure_delete(file_path)
            
            assert result is True
            assert not os.path.exists(file_path)


class TestSecureFileManagerHashing:
    """Test SecureFileManager file hashing methods."""
    
    def test_calculate_file_hash_basic(self):
        """Test basic file hash calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "hash_test.txt")
            content = b"content for hash testing"
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Calculate hash
            file_hash = SecureFileManager.calculate_file_hash(file_path)
            
            # Verify hash
            expected_hash = hashlib.sha256(content).hexdigest()
            assert file_hash == expected_hash
    
    def test_calculate_file_hash_algorithms(self):
        """Test file hash calculation with different algorithms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "hash_algo_test.txt")
            content = b"algorithm test content"
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Test different algorithms
            algorithms = ['sha256', 'sha1', 'md5', 'sha512']
            
            for algorithm in algorithms:
                file_hash = SecureFileManager.calculate_file_hash(file_path, algorithm)
                expected_hash = hashlib.new(algorithm, content).hexdigest()
                assert file_hash == expected_hash
    
    def test_calculate_file_hash_large_file(self):
        """Test file hash calculation for large files (chunked reading)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "large_hash_test.txt")
            
            # Create 1MB file with pattern
            chunk = b"ABCDEFGHIJKLMNOP" * 4096  # 64KB chunk
            content = chunk * 16  # 1MB total
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Calculate hash
            file_hash = SecureFileManager.calculate_file_hash(file_path)
            
            # Verify against expected hash
            expected_hash = hashlib.sha256(content).hexdigest()
            assert file_hash == expected_hash
    
    def test_calculate_file_hash_empty_file(self):
        """Test file hash calculation for empty files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "empty_hash_test.txt")
            
            # Create empty file
            Path(file_path).touch()

            # Calculate hash
            file_hash = SecureFileManager.calculate_file_hash(file_path)
            
            # Verify against expected empty file hash
            expected_hash = hashlib.sha256(b'').hexdigest()
            assert file_hash == expected_hash
    
    def test_calculate_file_hash_nonexistent_file(self):
        """Test file hash calculation for non-existent files."""
        with pytest.raises(FileSystemSecurityError) as exc_info:
            SecureFileManager.calculate_file_hash("/nonexistent/file.txt")
        assert "Failed to calculate file hash" in str(exc_info.value)
    
    def test_calculate_file_hash_invalid_algorithm(self):
        """Test file hash calculation with invalid algorithm."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "invalid_algo_test.txt")
            
            with open(file_path, 'wb') as f:
                f.write(b"test content")
            
            with pytest.raises(FileSystemSecurityError):
                SecureFileManager.calculate_file_hash(file_path, "invalid_algorithm")


class TestSecureFileManagerIntegration:
    """Test integration scenarios and edge cases."""
    
    def test_create_validate_delete_workflow(self):
        """Test complete workflow: create, validate, then securely delete."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "workflow_test.txt")
            content = b"workflow test content"
            
            # Create secure file
            result_path = SecureFileManager.create_secure_file(file_path, content)
            
            # Validate permissions
            validation_result = SecureFileManager.validate_file_permissions(result_path)
            assert validation_result is True
            
            # Validate size
            size_result = SecureFileManager.validate_file_size(result_path, max_size=1024)
            assert size_result is True
            
            # Calculate hash for integrity
            file_hash = SecureFileManager.calculate_file_hash(result_path)
            expected_hash = hashlib.sha256(content).hexdigest()
            assert file_hash == expected_hash
            
            # Securely delete
            delete_result = SecureFileManager.secure_delete(result_path)
            assert delete_result is True
            assert not os.path.exists(result_path)
    
    def test_concurrent_operations(self):
        """Test that operations are safe with concurrent access."""
        # This would require threading to test properly
        # For now, just ensure basic operations don't interfere
        with tempfile.TemporaryDirectory() as temp_dir:
            files = []
            
            # Create multiple files
            for i in range(10):
                file_path = os.path.join(temp_dir, f"concurrent_{i}.txt")
                content = f"concurrent content {i}".encode()
                
                result_path = SecureFileManager.create_secure_file(file_path, content)
                files.append(result_path)
            
            # Verify all files exist
            for file_path in files:
                assert os.path.exists(file_path)
            
            # Delete all files
            for file_path in files:
                result = SecureFileManager.secure_delete(file_path)
                assert result is True
    
    def test_path_resolution(self):
        """Test proper path resolution and normalization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save current directory
            original_cwd = os.getcwd()
            
            try:
                # Test with relative paths
                os.chdir(temp_dir)
                
                relative_path = "relative_test.txt"
                content = b"relative path test"
                
                result_path = SecureFileManager.create_secure_file(relative_path, content)
                
                # Should resolve to absolute path
                assert os.path.isabs(result_path)
                assert os.path.exists(result_path)
                
                # Clean up explicitly before directory cleanup
                SecureFileManager.secure_delete(result_path)
                
            finally:
                # Always restore original directory
                os.chdir(original_cwd)
    
    def test_error_message_security(self):
        """Test that error messages don't leak sensitive information."""
        import platform
        
        if platform.system() == 'Windows':
            # On Windows, try to create a file with an invalid name
            sensitive_path = "C:\\invalid<path>secret_api_key_12345.txt"
        else:
            # On Unix, try to create file in a protected directory
            sensitive_path = "/root/secret_api_key_12345.txt"
        
        with pytest.raises(FileSystemSecurityError) as exc_info:
            SecureFileManager.create_secure_file(sensitive_path, b"content")
        
        # Error message should be generic
        error_msg = str(exc_info.value)
        assert "Failed to create secure file" in error_msg
        # Should not contain the sensitive path details in raw form
        assert "secret_api_key_12345" not in error_msg.lower()


if __name__ == "__main__":
    pytest.main([__file__])
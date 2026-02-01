import os
import stat
import hashlib
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict
import secrets


class FileSystemSecurityError(Exception):
    """Raised when file system security validation fails."""
    pass


class SecureFileManager:
    """Secure file operations with permission validation and integrity checks."""
    
    @staticmethod
    def create_secure_file(file_path: str, content: bytes, permissions: int = 0o600) -> str:
        """Create file with secure permissions atomically."""
        
        file_path = Path(file_path).resolve()
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create temporary file in same directory for atomic move
            temp_fd, temp_path = tempfile.mkstemp(
                dir=file_path.parent,
                prefix=f".{file_path.name}.",
                suffix=".tmp"
            )
            # Write content first, then set permissions
            with os.fdopen(temp_fd, 'wb') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            # temp_fd is now closed by the with statement
            
            # Set secure permissions after closing file handle
            # Use os.chmod instead of os.fchmod for Windows compatibility
            os.chmod(temp_path, permissions)
            
            # Atomic move to final location
            os.replace(temp_path, file_path)
            
            logging.debug(f"Securely created file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            # Clean up temporary file on failure if it was created
            try:
                os.unlink(temp_path)
            except (OSError, NameError):
                pass
            # Don't expose sensitive path information in error messages
            raise FileSystemSecurityError(f"Failed to create secure file: {type(e).__name__}")
    
    @staticmethod
    def secure_delete(file_path: str, passes: int = 3) -> bool:
        """Securely delete file by overwriting before removal."""
        
        if not os.path.exists(file_path):
            return True
        
        file_path = Path(file_path).resolve()
        
        try:
            # Get file size
            file_size = file_path.stat().st_size
            
            with open(file_path, 'r+b') as f:
                for _ in range(passes):
                    # Seek to beginning
                    f.seek(0)
                    
                    # Overwrite with random data
                    remaining = file_size
                    while remaining > 0:
                        chunk_size = min(remaining, 64 * 1024)  # 64KB chunks
                        f.write(os.urandom(chunk_size))
                        remaining -= chunk_size
                    
                    # Flush to disk
                    f.flush()
                    os.fsync(f.fileno())
            
            # Finally remove the file
            os.unlink(file_path)
            
            logging.debug(f"Securely deleted file: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to securely delete {file_path}: {e}")
            return False
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
        """Calculate file hash for integrity verification."""
        
        try:
            hasher = hashlib.new(algorithm)
        except ValueError as e:
            raise FileSystemSecurityError(f"Unsupported hash algorithm '{algorithm}': {e}")
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(64 * 1024), b''):
                    hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except Exception as e:
            raise FileSystemSecurityError(f"Failed to calculate file hash: {e}")
    
    @staticmethod
    def validate_file_size(file_path: str, max_size: int) -> bool:
        """Validate file size to prevent DoS attacks."""
        
        if not os.path.exists(file_path):
            return False
        
        file_size = os.path.getsize(file_path)
        
        if file_size > max_size:
            raise FileSystemSecurityError(
                f"File too large: {file_size} bytes (max: {max_size})"
            )
        
        return True
    
    @staticmethod
    def validate_file_permissions(file_path: str, required_perms: int = 0o600) -> bool:
        """Validate that file has secure permissions.

        Returns:
            True if permissions are valid, False if file does not exist.

        Raises:
            FileSystemSecurityError: If permissions are insecure or cannot be checked.
        """
        import platform

        if not os.path.exists(file_path):
            return False

        # On Windows, permission checking is different
        if platform.system() == 'Windows':
            # Basic existence check for Windows - full permission model is complex
            try:
                with open(file_path, 'r'):
                    pass  # Verify file is accessible
                return True
            except PermissionError:
                raise FileSystemSecurityError(f"File permissions too restrictive: {file_path}")

        # Unix-like systems
        file_stat = os.stat(file_path)
        file_perms = file_stat.st_mode & 0o777

        # Check if permissions are at least as restrictive as required
        if file_perms & ~required_perms:
            raise FileSystemSecurityError(
                f"File permissions too permissive: {oct(file_perms)} (required: {oct(required_perms)})"
            )

        return True
import re
import logging
import hashlib
from typing import Any, Optional, Union, List
from pathlib import Path
import os


class SecurityValidationError(Exception):
    """Raised when security validation fails."""
    def __init__(self, message: str, field: str = None, value: str = None):
        self.field = field
        self.value_hash = hashlib.sha256(str(value).encode()).hexdigest()[:8] if value else None
        super().__init__(message)


class InputValidator:
    """Centralized input validation for security."""
    
    # Security patterns
    SAFE_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9._/-]{1,255}$')
    PATH_TRAVERSAL_PATTERN = re.compile(r'\.\.[\\/]|[\\/]\.\.|^\.\.[\\/]|[\\/]\.\.$')
    SCRIPT_INJECTION_PATTERN = re.compile(r'<script|javascript:|on\w+\s*=|eval\s*\(', re.IGNORECASE)
    
    @classmethod
    def validate_secret_key(cls, key: str) -> str:
        """Validate secret key name for security and format compliance."""
        
        if not isinstance(key, str):
            raise SecurityValidationError("Secret key must be string", "key")
        
        if not key or key.isspace():
            raise SecurityValidationError("Secret key cannot be empty", "key")
        
        if len(key) > 255:
            raise SecurityValidationError("Secret key too long (max 255 chars)", "key", key)
        
        if len(key) < 1:
            raise SecurityValidationError("Secret key too short (min 1 char)", "key", key)
        
        # Check for path traversal attempts
        if cls.PATH_TRAVERSAL_PATTERN.search(key):
            raise SecurityValidationError("Path traversal detected in key", "key", key)
        
        # Check for valid characters only
        if not cls.SAFE_KEY_PATTERN.match(key):
            raise SecurityValidationError("Invalid characters in secret key", "key", key)
        
        # Check for reserved names
        reserved_names = {
            'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5',
            'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4',
            'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
        }
        if key.lower() in reserved_names:
            raise SecurityValidationError("Reserved key name not allowed", "key", key)
        
        return key
    
    @classmethod
    def validate_secret_value(cls, value: str, max_size: int = 64 * 1024) -> str:
        """Validate secret value for size and content."""
        
        if not isinstance(value, str):
            raise SecurityValidationError("Secret value must be string", "value")
        
        if len(value.encode('utf-8')) > max_size:
            raise SecurityValidationError(f"Secret value too large (max {max_size} bytes)", "value")
        
        if len(value) == 0:
            raise SecurityValidationError("Secret value cannot be empty", "value")
        
        # Check for script injection attempts
        if cls.SCRIPT_INJECTION_PATTERN.search(value):
            logging.warning("Potential script injection detected in secret value")
        
        return value
    
    @classmethod
    def validate_file_path(cls, file_path: str, allowed_dirs: List[str] = None) -> Path:
        """Validate file path for security."""
        
        if not isinstance(file_path, str):
            raise SecurityValidationError("File path must be string", "file_path")
        
        if not file_path or file_path.isspace():
            raise SecurityValidationError("File path cannot be empty", "file_path")
        
        # Convert to Path object for normalized handling
        path = Path(file_path).resolve()
        
        # Check for path traversal
        if cls.PATH_TRAVERSAL_PATTERN.search(file_path):
            raise SecurityValidationError("Path traversal detected", "file_path", file_path)
        
        # Validate against allowed directories if specified
        if allowed_dirs:
            allowed_paths = [Path(d).resolve() for d in allowed_dirs]
            if not any(str(path).startswith(str(allowed_path)) for allowed_path in allowed_paths):
                raise SecurityValidationError("Path not in allowed directories", "file_path", file_path)
        
        return path
    
    @classmethod
    def validate_yaml_content(cls, content: str, max_size: int = 10 * 1024 * 1024) -> str:
        """Validate YAML content for security."""
        
        if not isinstance(content, str):
            raise SecurityValidationError("YAML content must be string", "yaml_content")
        
        if len(content.encode('utf-8')) > max_size:
            raise SecurityValidationError(f"YAML content too large (max {max_size} bytes)", "yaml_content")
        
        # Check for billion laughs attack patterns
        entity_count = content.count('&')
        reference_count = content.count('*')
        if entity_count > 100 or reference_count > 100:
            raise SecurityValidationError("Excessive YAML references detected", "yaml_content")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            'eval', 'exec', 'import', '__import__', 'subprocess', 'os.system'
        ]
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                logging.warning(f"Suspicious pattern '{pattern}' detected in YAML")
        
        return content
    
    @classmethod
    def validate_configuration_key(cls, key: str) -> str:
        """Validate configuration key path (e.g., 'database.host')."""
        
        if not isinstance(key, str):
            raise SecurityValidationError("Configuration key must be string", "config_key")
        
        if not key or key.isspace():
            raise SecurityValidationError("Configuration key cannot be empty", "config_key")
        
        if len(key) > 500:
            raise SecurityValidationError("Configuration key too long", "config_key", key)
        
        # Allow alphanumeric, dots, underscores, hyphens
        if not re.match(r'^[a-zA-Z0-9._-]+$', key):
            raise SecurityValidationError("Invalid characters in configuration key", "config_key", key)
        
        # Prevent double dots or leading/trailing dots
        if '..' in key or key.startswith('.') or key.endswith('.'):
            raise SecurityValidationError("Invalid dot usage in configuration key", "config_key", key)
        
        return key
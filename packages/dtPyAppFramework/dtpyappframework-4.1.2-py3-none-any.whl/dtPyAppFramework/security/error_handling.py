import logging
import secrets
import hashlib
import traceback
import sys
import os
import time
from pathlib import Path
from typing import Any, Optional, Dict
from enum import Enum
from functools import wraps


class ErrorLevel(Enum):
    PUBLIC = "public"      # Safe for user display
    INTERNAL = "internal"  # Internal logs only
    SECURITY = "security"  # Security audit logs only


class SecureErrorHandler:
    """Secure error handling to prevent information leakage."""
    
    def __init__(self):
        # Create separate loggers for different security levels
        self.public_logger = logging.getLogger('public')
        self.internal_logger = logging.getLogger('internal')
        self.security_logger = logging.getLogger('security_audit')
        
        # Don't setup security logger immediately - do it lazily when needed
        self._security_logger_setup = False
    
    def _ensure_security_logger_setup(self):
        """Ensure security logger is setup (lazy initialization)."""
        if not self._security_logger_setup:
            self._setup_security_logger()
            self._security_logger_setup = True
    
    def _setup_security_logger(self):
        """Setup security audit logger with secure file handling."""
        try:
            # Try to get existing ApplicationPaths from ProcessManager
            app_paths = None
            app_short_name = 'dtpy_app'  # fallback
            
            try:
                from ..process import ProcessManager
                pm_instance = ProcessManager._instances.get(ProcessManager, None)
                if pm_instance and hasattr(pm_instance, 'application_paths') and pm_instance.application_paths:
                    app_paths = pm_instance.application_paths
                    app_short_name = pm_instance.short_name
            except Exception:
                pass
            
            # If we don't have ApplicationPaths from ProcessManager, create a minimal one
            if app_paths is None:
                from ..paths import ApplicationPaths
                app_paths = ApplicationPaths(app_short_name)
            security_log_path = os.path.join(
                app_paths.app_data_root_path,
                'security_audit.log'
            )
            
            # Try to create secure file, fallback to regular file if needed
            try:
                from .filesystem import SecureFileManager
                SecureFileManager.create_secure_file(
                    security_log_path,
                    b'',  # Empty initial content
                    permissions=0o600
                )
            except Exception:
                # Fallback to creating regular file if secure creation fails
                os.makedirs(os.path.dirname(security_log_path), exist_ok=True)
                # Just create an empty file if secure creation fails
                Path(security_log_path).touch()
            
            handler = logging.FileHandler(security_log_path)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
            ))
            
            self.security_logger.addHandler(handler)
            self.security_logger.setLevel(logging.WARNING)
        except Exception as e:
            # Fallback if ApplicationPaths is not available
            logging.error(f"Failed to setup security logger: {e}")
    
    def log_secret_operation_error(self, operation: str, key: str, error: Exception, 
                                 store_name: str = None) -> str:
        """Log secret operation error securely."""
        
        # Ensure security logger is setup
        self._ensure_security_logger_setup()
        
        # Generate correlation ID
        error_id = secrets.token_hex(8)
        
        # Hash sensitive information
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16] if key else "unknown"
        
        # Public log - minimal information
        if key:
            self.public_logger.error(
                f"Secret operation '{operation}' failed (Error ID: {error_id})"
            )
        else:
            self.public_logger.error(
                f"Secret store operation failed (Error ID: {error_id})"
            )
        
        # Internal log - more details but no sensitive data
        self.internal_logger.error(
            f"ErrorID: {error_id} | Operation: {operation} | "
            f"Store: {store_name or 'unknown'} | "
            f"KeyHash: {key_hash} | "
            f"ErrorType: {type(error).__name__}"
        )
        
        # Security audit log - full details for investigation
        self.security_logger.error(
            f"ErrorID: {error_id} | "
            f"Operation: {operation} | "
            f"Store: {store_name or 'unknown'} | "
            f"Key: {key} | "
            f"Error: {type(error).__name__}: {str(error)} | "
            f"PID: {os.getpid()} | "
            f"User: {os.getenv('USER', 'unknown')}"
        )
        
        return error_id

    def log_authentication_error(self, operation: str, target: str, error: Exception) -> str:
        """Log authentication error securely."""
        
        # Ensure security logger is setup
        self._ensure_security_logger_setup()
        
        # Generate correlation ID
        error_id = secrets.token_hex(8)
        
        # Public log - minimal information
        self.public_logger.error(
            f"Authentication failed for {operation} (Error ID: {error_id})"
        )
        
        # Internal log - more details but no sensitive data
        self.internal_logger.error(
            f"ErrorID: {error_id} | Operation: {operation} | "
            f"Target: {target} | "
            f"ErrorType: {type(error).__name__}"
        )
        
        # Security audit log - full details for investigation
        self.security_logger.error(
            f"ErrorID: {error_id} | "
            f"Operation: {operation} | "
            f"Target: {target} | "
            f"Error: {type(error).__name__}: {str(error)} | "
            f"PID: {os.getpid()} | "
            f"User: {os.getenv('USER', 'unknown')}"
        )
        
        return error_id

    def log_file_operation_error(self, operation: str, file_path: str, error: Exception) -> str:
        """Log file operation error securely."""
        
        # Ensure security logger is setup
        self._ensure_security_logger_setup()
        
        # Generate correlation ID
        error_id = secrets.token_hex(8)
        
        # Hash sensitive file path information
        path_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16] if file_path else "unknown"
        
        # Public log - minimal information
        self.public_logger.error(
            f"File operation '{operation}' failed (Error ID: {error_id})"
        )
        
        # Internal log - more details but no sensitive data
        self.internal_logger.error(
            f"ErrorID: {error_id} | Operation: {operation} | "
            f"PathHash: {path_hash} | "
            f"ErrorType: {type(error).__name__}"
        )
        
        # Security audit log - full details for investigation
        self.security_logger.error(
            f"ErrorID: {error_id} | "
            f"Operation: {operation} | "
            f"FilePath: {file_path} | "
            f"Error: {type(error).__name__}: {str(error)} | "
            f"PID: {os.getpid()} | "
            f"User: {os.getenv('USER', 'unknown')}"
        )
        
        return error_id


# Global error handler instance
secure_error_handler = SecureErrorHandler()


# Decorator for secure error handling
def secure_error_handling(operation: str):
    """Decorator for secure error handling in methods."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                # Import here to avoid circular imports
                from .validation import SecurityValidationError
                from .filesystem import FileSystemSecurityError
                
                if isinstance(e, SecurityValidationError):
                    error_id = secure_error_handler.log_secret_operation_error(
                        f"{operation}::{func.__name__}",
                        getattr(e, 'field', 'unknown'),
                        e,
                        getattr(e, 'value_hash', None)
                    )
                    raise SecurityValidationError(f"Validation failed (ID: {error_id})")
                
                elif isinstance(e, FileSystemSecurityError):
                    error_id = secure_error_handler.log_file_operation_error(
                        f"{operation}::{func.__name__}",
                        "filesystem",
                        e
                    )
                    raise FileSystemSecurityError(f"File operation failed (ID: {error_id})")
                
                else:
                    error_id = secure_error_handler.log_secret_operation_error(
                        f"{operation}::{func.__name__}",
                        "unknown",
                        e
                    )
                    raise type(e)(f"Operation failed (ID: {error_id})")
        
        return wrapper
    return decorator


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    return result == 0


def timing_safe_operation(operation_func, min_time: float = 0.1):
    """Execute operation with minimum time to prevent timing analysis."""
    start_time = time.time()
    
    try:
        result = operation_func()
        
        # Ensure minimum time to prevent timing analysis
        elapsed = time.time() - start_time
        if elapsed < min_time:
            time.sleep(min_time - elapsed)
        
        return result
        
    except Exception:
        # Always take the same minimum time even on error
        elapsed = time.time() - start_time
        if elapsed < min_time:
            time.sleep(min_time - elapsed)
        raise
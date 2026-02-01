"""
Comprehensive tests for logging configuration management.

This test suite ensures that the logging configuration system correctly handles
log levels, formatters, handlers, rotation settings, and provides proper
integration with the framework's multi-processing and cross-platform capabilities.
"""

import pytest
import os
import sys
import logging
from unittest.mock import patch, MagicMock

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.logging.default_logging import default_config


class TestDefaultLoggingConfig:
    """Test default logging configuration generation."""
    
    def test_default_config_basic(self):
        """Test basic default configuration generation."""
        config = default_config()
        
        # Verify structure
        assert config["version"] == 1
        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config
        assert "root" in config
    
    def test_default_config_with_log_level(self):
        """Test default configuration with custom log level."""
        config = default_config(log_level="DEBUG")
        
        # Verify log level is applied
        assert config["loggers"]["defaultLogger"]["level"] == "DEBUG"
        assert config["root"]["level"] == "DEBUG"
    
    def test_default_config_with_rotation_backup_count(self):
        """Test default configuration with custom rotation backup count."""
        config = default_config(rotation_backup_count=10)
        
        # Verify backup count is applied to all handlers
        assert config["handlers"]["logfile_ALL"]["backupCount"] == 10
        assert config["handlers"]["logfile_ERR"]["backupCount"] == 10
    
    def test_default_config_with_both_parameters(self):
        """Test default configuration with both parameters."""
        config = default_config(log_level="WARNING", rotation_backup_count=15)
        
        # Verify both parameters are applied
        assert config["loggers"]["defaultLogger"]["level"] == "WARNING"
        assert config["root"]["level"] == "WARNING"
        assert config["handlers"]["logfile_ALL"]["backupCount"] == 15
        assert config["handlers"]["logfile_ERR"]["backupCount"] == 15


class TestLoggingFormatters:
    """Test logging formatter configuration."""
    
    def test_simple_file_formatter(self):
        """Test simple file formatter configuration."""
        config = default_config()
        formatter = config["formatters"]["simple_file"]
        
        # Verify formatter format includes all expected fields
        expected_fields = [
            "%(asctime)s",
            "%(levelname)s", 
            "%(processName)s",
            "%(process)d",
            "%(threadName)s",
            "%(thread)d",
            "%(module)s",
            "%(funcName)s",
            "%(lineno)d",
            "%(message)s"
        ]
        
        for field in expected_fields:
            assert field in formatter["format"]
    
    def test_formatter_fields_order(self):
        """Test that formatter fields are in expected order."""
        config = default_config()
        formatter_format = config["formatters"]["simple_file"]["format"]
        
        # Split by ' - ' to get field positions
        parts = formatter_format.split(" - ")
        
        # Verify order of key fields
        assert "%(asctime)s" in parts[0]
        assert "%(levelname)s" in parts[1]
        assert "%(processName)s" in parts[2] and "%(process)d" in parts[2]
        assert "%(threadName)s" in parts[3] and "%(thread)d" in parts[3]
        assert "%(module)s" in parts[4] and "%(funcName)s" in parts[4] and "%(lineno)d" in parts[4]
        assert "%(message)s" in parts[5]


class TestLoggingHandlers:
    """Test logging handler configuration."""
    
    def test_logfile_all_handler(self):
        """Test logfile_ALL handler configuration."""
        config = default_config()
        handler = config["handlers"]["logfile_ALL"]
        
        # Verify handler configuration
        assert handler["class"] == "logging.handlers.TimedRotatingFileHandler"
        assert handler["level"] == "DEBUG"
        assert handler["formatter"] == "simple_file"
        assert handler["filename"] == ""  # Should be empty for later configuration
        assert handler["when"] == "D"  # Daily rotation
        assert handler["interval"] == 1
        assert handler["encoding"] == "utf8"
        assert handler["backupCount"] == 5  # Default value
    
    def test_logfile_err_handler(self):
        """Test logfile_ERR handler configuration."""
        config = default_config()
        handler = config["handlers"]["logfile_ERR"]
        
        # Verify handler configuration
        assert handler["class"] == "logging.handlers.TimedRotatingFileHandler"
        assert handler["level"] == "ERROR"  # Only ERROR and above
        assert handler["formatter"] == "simple_file"
        assert handler["filename"] == ""  # Should be empty for later configuration
        assert handler["when"] == "D"  # Daily rotation
        assert handler["interval"] == 1
        assert handler["encoding"] == "utf8"
        assert handler["backupCount"] == 5  # Default value
    
    def test_handler_rotation_settings(self):
        """Test handler rotation settings."""
        config = default_config(rotation_backup_count=7)
        
        all_handler = config["handlers"]["logfile_ALL"]
        err_handler = config["handlers"]["logfile_ERR"]
        
        # Both handlers should have same rotation settings
        for handler in [all_handler, err_handler]:
            assert handler["when"] == "D"  # Daily
            assert handler["interval"] == 1  # Every day
            assert handler["backupCount"] == 7  # Custom backup count
            assert handler["encoding"] == "utf8"
    
    def test_handler_file_names_empty(self):
        """Test that handler filenames are initially empty."""
        config = default_config()
        
        # Filenames should be empty strings for runtime configuration
        assert config["handlers"]["logfile_ALL"]["filename"] == ""
        assert config["handlers"]["logfile_ERR"]["filename"] == ""


class TestLoggingLoggers:
    """Test logger configuration."""
    
    def test_default_logger_configuration(self):
        """Test defaultLogger configuration."""
        config = default_config(log_level="INFO")
        logger = config["loggers"]["defaultLogger"]
        
        # Verify logger configuration
        assert logger["level"] == "INFO"
        assert logger["handlers"] == ["logfile_ALL", "logfile_ERR"]
        assert logger["propagate"] == "no"
    
    def test_root_logger_configuration(self):
        """Test root logger configuration."""
        config = default_config(log_level="DEBUG")
        root = config["root"]
        
        # Verify root logger configuration
        assert root["level"] == "DEBUG"
        assert root["handlers"] == ["logfile_ALL", "logfile_ERR"]
    
    def test_logger_handler_references(self):
        """Test that loggers reference correct handlers."""
        config = default_config()
        
        default_logger = config["loggers"]["defaultLogger"]
        root_logger = config["root"]
        
        # Both loggers should reference both handlers
        expected_handlers = ["logfile_ALL", "logfile_ERR"]
        assert default_logger["handlers"] == expected_handlers
        assert root_logger["handlers"] == expected_handlers
        
        # Verify referenced handlers exist
        for handler_name in expected_handlers:
            assert handler_name in config["handlers"]


class TestLoggingLevels:
    """Test different logging levels."""
    
    def test_debug_level(self):
        """Test configuration with DEBUG level."""
        config = default_config(log_level="DEBUG")
        
        # Verify DEBUG level is set
        assert config["loggers"]["defaultLogger"]["level"] == "DEBUG"
        assert config["root"]["level"] == "DEBUG"
        
        # Handler levels should remain unchanged
        assert config["handlers"]["logfile_ALL"]["level"] == "DEBUG"
        assert config["handlers"]["logfile_ERR"]["level"] == "ERROR"
    
    def test_info_level(self):
        """Test configuration with INFO level."""
        config = default_config(log_level="INFO")
        
        assert config["loggers"]["defaultLogger"]["level"] == "INFO"
        assert config["root"]["level"] == "INFO"
    
    def test_warning_level(self):
        """Test configuration with WARNING level."""
        config = default_config(log_level="WARNING")
        
        assert config["loggers"]["defaultLogger"]["level"] == "WARNING"
        assert config["root"]["level"] == "WARNING"
    
    def test_error_level(self):
        """Test configuration with ERROR level."""
        config = default_config(log_level="ERROR")
        
        assert config["loggers"]["defaultLogger"]["level"] == "ERROR"
        assert config["root"]["level"] == "ERROR"
    
    def test_critical_level(self):
        """Test configuration with CRITICAL level."""
        config = default_config(log_level="CRITICAL")
        
        assert config["loggers"]["defaultLogger"]["level"] == "CRITICAL"
        assert config["root"]["level"] == "CRITICAL"
    
    def test_handler_level_independence(self):
        """Test that handler levels are independent of logger levels."""
        config = default_config(log_level="CRITICAL")
        
        # Logger level changes, but handler levels remain fixed
        assert config["loggers"]["defaultLogger"]["level"] == "CRITICAL"
        assert config["handlers"]["logfile_ALL"]["level"] == "DEBUG"  # Always DEBUG
        assert config["handlers"]["logfile_ERR"]["level"] == "ERROR"  # Always ERROR


class TestLoggingRotation:
    """Test logging rotation configuration."""
    
    def test_default_rotation_settings(self):
        """Test default rotation settings."""
        config = default_config()
        
        for handler_name in ["logfile_ALL", "logfile_ERR"]:
            handler = config["handlers"][handler_name]
            assert handler["when"] == "D"  # Daily
            assert handler["interval"] == 1  # Every 1 day
            assert handler["backupCount"] == 5  # Keep 5 backups
    
    def test_custom_backup_count(self):
        """Test custom backup count settings."""
        test_cases = [1, 3, 7, 14, 30, 365]
        
        for backup_count in test_cases:
            config = default_config(rotation_backup_count=backup_count)
            
            for handler_name in ["logfile_ALL", "logfile_ERR"]:
                handler = config["handlers"][handler_name]
                assert handler["backupCount"] == backup_count
    
    def test_zero_backup_count(self):
        """Test zero backup count (no rotation)."""
        config = default_config(rotation_backup_count=0)
        
        for handler_name in ["logfile_ALL", "logfile_ERR"]:
            handler = config["handlers"][handler_name]
            assert handler["backupCount"] == 0
    
    def test_rotation_consistency(self):
        """Test that rotation settings are consistent across handlers."""
        config = default_config(rotation_backup_count=10)
        
        all_handler = config["handlers"]["logfile_ALL"]
        err_handler = config["handlers"]["logfile_ERR"]
        
        # Both handlers should have identical rotation settings
        rotation_fields = ["when", "interval", "backupCount"]
        for field in rotation_fields:
            assert all_handler[field] == err_handler[field]


class TestLoggingConfigurationIntegration:
    """Test logging configuration integration scenarios."""
    
    def test_production_configuration(self):
        """Test production-like logging configuration."""
        config = default_config(log_level="INFO", rotation_backup_count=30)
        
        # Verify production settings
        assert config["loggers"]["defaultLogger"]["level"] == "INFO"
        assert config["root"]["level"] == "INFO"
        
        # Long retention for production
        for handler_name in ["logfile_ALL", "logfile_ERR"]:
            handler = config["handlers"][handler_name]
            assert handler["backupCount"] == 30
            assert handler["encoding"] == "utf8"
            assert handler["when"] == "D"  # Daily rotation
    
    def test_development_configuration(self):
        """Test development-like logging configuration."""
        config = default_config(log_level="DEBUG", rotation_backup_count=3)
        
        # Verify development settings
        assert config["loggers"]["defaultLogger"]["level"] == "DEBUG"
        assert config["root"]["level"] == "DEBUG"
        
        # Short retention for development
        for handler_name in ["logfile_ALL", "logfile_ERR"]:
            handler = config["handlers"][handler_name]
            assert handler["backupCount"] == 3
    
    def test_high_volume_configuration(self):
        """Test configuration for high-volume logging scenarios."""
        config = default_config(log_level="WARNING", rotation_backup_count=7)
        
        # Higher log level to reduce volume
        assert config["loggers"]["defaultLogger"]["level"] == "WARNING"
        
        # Moderate retention
        for handler_name in ["logfile_ALL", "logfile_ERR"]:
            handler = config["handlers"][handler_name]
            assert handler["backupCount"] == 7
    
    def test_multi_process_compatibility(self):
        """Test that configuration is compatible with multi-process scenarios."""
        config = default_config()
        
        # Verify formatter includes process information
        formatter_format = config["formatters"]["simple_file"]["format"]
        assert "%(processName)s" in formatter_format
        assert "%(process)d" in formatter_format
        assert "%(threadName)s" in formatter_format
        assert "%(thread)d" in formatter_format
        
        # Verify handlers use TimedRotatingFileHandler (process-safe)
        for handler_name in ["logfile_ALL", "logfile_ERR"]:
            handler = config["handlers"][handler_name]
            assert handler["class"] == "logging.handlers.TimedRotatingFileHandler"


class TestLoggingConfigurationEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_very_high_backup_count(self):
        """Test configuration with very high backup count."""
        config = default_config(rotation_backup_count=1000)
        
        for handler_name in ["logfile_ALL", "logfile_ERR"]:
            handler = config["handlers"][handler_name]
            assert handler["backupCount"] == 1000
    
    def test_unusual_log_levels(self):
        """Test configuration with unusual but valid log levels."""
        unusual_levels = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in unusual_levels:
            config = default_config(log_level=level)
            assert config["loggers"]["defaultLogger"]["level"] == level
            assert config["root"]["level"] == level
    
    def test_configuration_immutability(self):
        """Test that configuration objects are independent."""
        config1 = default_config(log_level="DEBUG", rotation_backup_count=5)
        config2 = default_config(log_level="ERROR", rotation_backup_count=10)
        
        # Configurations should be independent
        assert config1["loggers"]["defaultLogger"]["level"] == "DEBUG"
        assert config2["loggers"]["defaultLogger"]["level"] == "ERROR"
        
        assert config1["handlers"]["logfile_ALL"]["backupCount"] == 5
        assert config2["handlers"]["logfile_ALL"]["backupCount"] == 10
    
    def test_configuration_structure_completeness(self):
        """Test that configuration has all required structure."""
        config = default_config()
        
        # Top-level keys
        required_top_level = ["version", "formatters", "handlers", "loggers", "root"]
        for key in required_top_level:
            assert key in config
        
        # Formatters
        assert "simple_file" in config["formatters"]
        assert "format" in config["formatters"]["simple_file"]
        
        # Handlers
        required_handlers = ["logfile_ALL", "logfile_ERR"]
        for handler_name in required_handlers:
            assert handler_name in config["handlers"]
            handler = config["handlers"][handler_name]
            
            required_handler_keys = [
                "class", "level", "formatter", "filename", 
                "when", "interval", "encoding", "backupCount"
            ]
            for key in required_handler_keys:
                assert key in handler
        
        # Loggers
        assert "defaultLogger" in config["loggers"]
        default_logger = config["loggers"]["defaultLogger"]
        required_logger_keys = ["level", "handlers", "propagate"]
        for key in required_logger_keys:
            assert key in default_logger
        
        # Root logger
        required_root_keys = ["level", "handlers"]
        for key in required_root_keys:
            assert key in config["root"]


class TestLoggingConfigurationCompatibility:
    """Test compatibility with Python logging system."""
    
    def test_logging_dictconfig_compatibility(self):
        """Test that configuration is compatible with logging.dictConfig."""
        import logging.config
        
        config = default_config()
        
        # This should not raise an exception
        try:
            # Validate the configuration structure
            # We can't actually apply it without file paths, but we can validate structure
            assert isinstance(config, dict)
            assert config["version"] == 1
            
            # Verify handler classes are valid
            for handler_name, handler_config in config["handlers"].items():
                handler_class = handler_config["class"]
                # Should be a valid Python module path
                assert "." in handler_class
                
                # Should reference valid formatter
                formatter_name = handler_config["formatter"]
                assert formatter_name in config["formatters"]
            
            # Verify logger handler references
            for logger_name, logger_config in config["loggers"].items():
                for handler_ref in logger_config["handlers"]:
                    assert handler_ref in config["handlers"]
            
            # Verify root logger handler references
            for handler_ref in config["root"]["handlers"]:
                assert handler_ref in config["handlers"]
                
        except Exception as e:
            pytest.fail(f"Configuration should be compatible with logging.dictConfig: {e}")
    
    def test_formatter_compatibility(self):
        """Test that formatter string is compatible with logging format."""
        import logging
        
        config = default_config()
        formatter_format = config["formatters"]["simple_file"]["format"]
        
        # Should be able to create a Formatter with this format
        try:
            logging.Formatter(formatter_format)
        except Exception as e:
            pytest.fail(f"Formatter string should be valid: {e}")
    
    def test_handler_class_validity(self):
        """Test that handler classes are valid and importable."""
        config = default_config()
        
        for handler_name, handler_config in config["handlers"].items():
            handler_class_path = handler_config["class"]
            
            # Should be able to import the handler class
            try:
                module_path, class_name = handler_class_path.rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                handler_class = getattr(module, class_name)
                
                # Should be a subclass of logging.Handler
                assert issubclass(handler_class, logging.Handler)
                
            except (ImportError, AttributeError) as e:
                pytest.fail(f"Handler class {handler_class_path} should be importable: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
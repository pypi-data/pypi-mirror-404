"""
Comprehensive tests for ApplicationPaths cross-platform path management.

This test suite ensures that ApplicationPaths correctly manages application directories
across different operating systems (Windows, macOS, Linux) and handles various
configuration scenarios including development mode and spawned instances.
"""

import pytest
import os
import sys
import tempfile
import shutil
import platform
from unittest.mock import patch, MagicMock

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.paths import ApplicationPaths


def _clear_singleton_cache():
    """Clear the singleton instance cache for ApplicationPaths.

    The @singleton() decorator stores instances in a closure-scoped dict.
    We access it via __closure__ to reset between tests.
    """
    if hasattr(ApplicationPaths, '__closure__') and ApplicationPaths.__closure__:
        for cell in ApplicationPaths.__closure__:
            try:
                contents = cell.cell_contents
                if isinstance(contents, dict):
                    contents.clear()
                    return
            except ValueError:
                continue


ENV_VARS_TO_CLEAR = [
    'DEV_MODE', 'CONTAINER_MODE',
    'dt_LOGGING_PATH', 'dt_APP_DATA', 'dt_USR_DATA', 'dt_TMP',
    'XDG_STATE_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME',
]


def _clean_env():
    """Remove test-related environment variables."""
    for var in ENV_VARS_TO_CLEAR:
        os.environ.pop(var, None)


class TestApplicationPathsBasic:
    """Test basic ApplicationPaths functionality and initialization."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()

    def teardown_method(self):
        self.setup_method()
    
    def test_basic_initialization(self):
        """Test basic ApplicationPaths initialization with required parameters."""
        app_paths = ApplicationPaths("TestApp")
        
        # Verify basic attributes are set
        assert app_paths.app_short_name == "TestApp"
        assert app_paths.forced_os is None
        assert app_paths.spawned_instance is False
        assert app_paths.auto_create is True
        assert app_paths.clean_temp is True
        assert app_paths.forced_dev_mode is False
        assert app_paths.worker_id is None
        
        # Verify paths are initialized
        assert app_paths.logging_root_path is not None
        assert app_paths.app_data_root_path is not None
        assert app_paths.usr_data_root_path is not None
        assert app_paths.tmp_root_path is not None
    
    def test_initialization_with_all_parameters(self):
        """Test ApplicationPaths initialization with all parameters specified."""
        app_paths = ApplicationPaths(
            app_short_name="TestApp",
            forced_os="TestOS",
            forced_dev_mode=True,
            auto_create=False,
            clean_temp=False,
            spawned_instance=True,
            worker_id=42
        )
        
        assert app_paths.app_short_name == "TestApp"
        assert app_paths.forced_os == "TestOS"
        assert app_paths.spawned_instance is True
        assert app_paths.auto_create is False
        assert app_paths.clean_temp is False
        assert app_paths.forced_dev_mode is True
        assert app_paths.worker_id == 42
        assert os.environ.get('DEV_MODE') == "True"


class TestApplicationPathsWindows:
    """Test Windows-specific path generation."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()

    def teardown_method(self):
        self.setup_method()
    
    @patch.dict(os.environ, {
        'LOCALAPPDATA': 'C:\\Users\\TestUser\\AppData\\Local',
        'ALLUSERSPROFILE': 'C:\\ProgramData',
        'APPDATA': 'C:\\Users\\TestUser\\AppData\\Roaming',
        'TEMP': 'C:\\Users\\TestUser\\AppData\\Local\\Temp'
    })
    def test_windows_paths_production_mode(self):
        """Test Windows path generation in production mode."""
        with patch('platform.system', return_value='Windows'):
            app_paths = ApplicationPaths("TestApp", forced_os="Windows", auto_create=False)

            # Use os.path.join for expected values because the source does the same,
            # and os.path.join uses platform-native separators (/ on Linux, \ on Windows).
            expected_logging = os.path.join('C:\\Users\\TestUser\\AppData\\Local', 'TestApp', 'logs')
            expected_app_data = os.path.join('C:\\ProgramData', 'TestApp')
            expected_usr_data = os.path.join('C:\\Users\\TestUser\\AppData\\Roaming', 'TestApp')
            expected_temp = os.path.join('C:\\Users\\TestUser\\AppData\\Local\\Temp', 'TestApp')

            assert app_paths.logging_root_path == expected_logging
            assert app_paths.app_data_root_path == expected_app_data
            assert app_paths.usr_data_root_path == expected_usr_data
            assert app_paths.tmp_root_path == expected_temp

            # Verify environment variables are set
            assert os.environ['dt_LOGGING_PATH'] == expected_logging
            assert os.environ['dt_APP_DATA'] == expected_app_data
            assert os.environ['dt_USR_DATA'] == expected_usr_data
            assert os.environ['dt_TMP'] == expected_temp
    
    def test_windows_paths_dev_mode(self):
        """Test Windows path generation in development mode."""
        with patch('os.getcwd', return_value='C:\\dev\\myproject'):
            app_paths = ApplicationPaths("TestApp", forced_dev_mode=True, auto_create=False)

            cwd = 'C:\\dev\\myproject'
            expected_logging = os.path.join(cwd, 'logs')
            expected_app_data = os.path.join(cwd, 'data', 'app')
            expected_usr_data = os.path.join(cwd, 'data', 'usr')
            expected_temp = os.path.join(cwd, 'temp')

            assert app_paths.logging_root_path == expected_logging
            assert app_paths.app_data_root_path == expected_app_data
            assert app_paths.usr_data_root_path == expected_usr_data
            assert app_paths.tmp_root_path == expected_temp


class TestApplicationPathsLinux:
    """Test Linux-specific path generation."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()

    def teardown_method(self):
        self.setup_method()

    def test_linux_paths_root_mode(self):
        """Test Linux path generation when running as root."""
        # Patch on __wrapped__ (the actual class) since ApplicationPaths is a singleton wrapper
        with patch('os.path.expanduser') as mock_expanduser:
            mock_expanduser.side_effect = lambda path: path.replace('~', '/root')
            with patch.object(ApplicationPaths.__wrapped__, '_is_root', return_value=True):
                app_paths = ApplicationPaths("TestApp", forced_os="Linux", auto_create=False)

                assert app_paths.logging_root_path == os.path.join('/var/log', 'TestApp')
                assert app_paths.app_data_root_path == os.path.join('/var/lib', 'TestApp')
                assert app_paths.usr_data_root_path == os.path.join('/etc', 'TestApp')

    def test_linux_paths_non_root_mode(self):
        """Test Linux path generation when running as a regular user (XDG defaults)."""
        with patch('os.path.expanduser') as mock_expanduser:
            mock_expanduser.side_effect = lambda path: path.replace('~', '/home/testuser')
            with patch.object(ApplicationPaths.__wrapped__, '_is_root', return_value=False):
                app_paths = ApplicationPaths("TestApp", forced_os="Linux", auto_create=False)

                expected_logging = os.path.join('/home/testuser/.local/state', 'TestApp', 'log')
                expected_app_data = os.path.join('/home/testuser/.config', 'TestApp')
                expected_usr_data = os.path.join('/home/testuser/.local/share', 'TestApp')

                assert app_paths.logging_root_path == expected_logging
                assert app_paths.app_data_root_path == expected_app_data
                assert app_paths.usr_data_root_path == expected_usr_data

    def test_linux_paths_xdg_overrides(self):
        """Test Linux path generation respects XDG environment variables."""
        with patch.object(ApplicationPaths.__wrapped__, '_is_root', return_value=False):
            with patch.dict(os.environ, {
                'XDG_STATE_HOME': '/custom/state',
                'XDG_CONFIG_HOME': '/custom/config',
                'XDG_DATA_HOME': '/custom/data',
            }):
                app_paths = ApplicationPaths("TestApp", forced_os="Linux", auto_create=False)

                assert app_paths.logging_root_path == os.path.join('/custom/state', 'TestApp', 'log')
                assert app_paths.app_data_root_path == os.path.join('/custom/config', 'TestApp')
                assert app_paths.usr_data_root_path == os.path.join('/custom/data', 'TestApp')

    def test_linux_temp_uses_tempfile(self):
        """Test Linux temp path uses tempfile.gettempdir()."""
        with patch('tempfile.gettempdir', return_value='/tmp'):
            with patch.object(ApplicationPaths.__wrapped__, '_is_root', return_value=False):
                app_paths = ApplicationPaths("TestApp", forced_os="Linux", auto_create=False)
                assert app_paths.tmp_root_path == os.path.join('/tmp', 'TestApp')


class TestApplicationPathsDarwin:
    """Test macOS (Darwin) specific path generation."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()

    def teardown_method(self):
        self.setup_method()
    
    @patch.dict(os.environ, {'TMPDIR': '/tmp/'})
    def test_darwin_paths_production_mode(self):
        """Test macOS path generation in production mode."""
        with patch('os.path.expanduser') as mock_expanduser:
            mock_expanduser.side_effect = lambda path: path.replace('~', '/Users/testuser')

            app_paths = ApplicationPaths("TestApp", forced_os="Darwin", auto_create=False)

            expected_logging = os.path.join('/Users/testuser/Library/Logs', 'TestApp')
            expected_app_data = os.path.join('/Library/Application Support', 'TestApp')
            expected_usr_data = os.path.join('/Users/testuser/Library/Application Support', 'TestApp')
            expected_temp = os.path.join('/tmp/', 'TestApp')

            assert app_paths.logging_root_path == expected_logging
            assert app_paths.app_data_root_path == expected_app_data
            assert app_paths.usr_data_root_path == expected_usr_data
            assert app_paths.tmp_root_path == expected_temp


class TestApplicationPathsSpawnedInstance:
    """Test spawned instance functionality with worker IDs."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()

    def teardown_method(self):
        self.setup_method()
    
    def test_spawned_instance_temp_path(self):
        """Test that spawned instances get worker-specific temp paths."""
        with patch('os.path.expanduser', side_effect=lambda path: path.replace('~', '/home/testuser')):
            with patch.object(ApplicationPaths.__wrapped__, '_is_root', return_value=False):
                with patch('tempfile.gettempdir', return_value='/tmp'):
                    app_paths = ApplicationPaths(
                        "TestApp",
                        forced_os="Linux",
                        spawned_instance=True,
                        worker_id=123,
                        auto_create=False
                    )

                    # Only temp path should include worker ID
                    assert app_paths.tmp_root_path == os.path.join('/tmp', 'TestApp', '123')
                    assert app_paths.logging_root_path == os.path.join('/home/testuser/.local/state', 'TestApp', 'log')
                    assert app_paths.app_data_root_path == os.path.join('/home/testuser/.config', 'TestApp')
                    assert app_paths.usr_data_root_path == os.path.join('/home/testuser/.local/share', 'TestApp')

    def test_spawned_instance_without_worker_id(self):
        """Test spawned instance behavior when worker_id is None."""
        with patch('tempfile.gettempdir', return_value='/tmp'):
            with patch.object(ApplicationPaths.__wrapped__, '_is_root', return_value=True):
                app_paths = ApplicationPaths(
                    "TestApp",
                    forced_os="Linux",
                    spawned_instance=True,
                    worker_id=None,
                    auto_create=False
                )

                # Should append 'None' as string since spawned_instance is True
                assert app_paths.tmp_root_path == os.path.join('/tmp', 'TestApp', 'None')


class TestApplicationPathsDirectoryManagement:
    """Test directory creation, cleanup, and management."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        _clear_singleton_cache()
        _clean_env()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_auto_create_directories(self):
        """Test automatic directory creation when auto_create=True."""
        with patch('os.getcwd', return_value=self.test_dir):
            app_paths = ApplicationPaths("TestApp", forced_dev_mode=True, auto_create=True)
            
            # Verify directories were created
            assert os.path.exists(app_paths.tmp_root_path)
            assert os.path.exists(app_paths.logging_root_path)
            assert os.path.exists(app_paths.usr_data_root_path)
            # app_data_root_path creation might fail in dev mode, that's expected
    
    def test_no_auto_create_directories(self):
        """Test that directories are not created when auto_create=False."""
        with patch('os.getcwd', return_value=self.test_dir):
            app_paths = ApplicationPaths("TestApp", forced_dev_mode=True, auto_create=False)
            
            # Verify directories were not created
            assert not os.path.exists(app_paths.tmp_root_path)
            assert not os.path.exists(app_paths.logging_root_path)
            assert not os.path.exists(app_paths.usr_data_root_path)
    
    def test_clean_temp_directory(self):
        """Test cleanup of existing temp directory when clean_temp=True."""
        with patch('os.getcwd', return_value=self.test_dir):
            # Create a temp directory with some content
            temp_path = os.path.join(self.test_dir, 'temp')
            os.makedirs(temp_path, exist_ok=True)
            test_file = os.path.join(temp_path, 'test_file.txt')
            with open(test_file, 'w') as f:
                f.write('test content')
            assert os.path.exists(test_file)
            
            # Initialize ApplicationPaths with clean_temp=True
            app_paths = ApplicationPaths(
                "TestApp", 
                forced_dev_mode=True, 
                clean_temp=True,
                auto_create=True
            )
            
            # Verify temp directory was cleaned and recreated
            assert os.path.exists(app_paths.tmp_root_path)
            assert not os.path.exists(test_file)  # Old content should be gone
    
    def test_no_clean_temp_directory(self):
        """Test that temp directory is preserved when clean_temp=False."""
        with patch('os.getcwd', return_value=self.test_dir):
            # Create a temp directory with some content
            temp_path = os.path.join(self.test_dir, 'temp')
            os.makedirs(temp_path, exist_ok=True)
            test_file = os.path.join(temp_path, 'test_file.txt')
            with open(test_file, 'w') as f:
                f.write('test content')
            assert os.path.exists(test_file)
            
            # Initialize ApplicationPaths with clean_temp=False
            _app_paths = ApplicationPaths(
                "TestApp",
                forced_dev_mode=True,
                clean_temp=False,
                auto_create=False
            )
            
            # Verify temp directory and content was preserved
            assert os.path.exists(test_file)  # Old content should remain


class TestApplicationPathsEnvironmentVariables:
    """Test environment variable management."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()

    def teardown_method(self):
        self.setup_method()
    
    def test_dev_mode_environment_variable(self):
        """Test that DEV_MODE environment variable is set when forced_dev_mode=True."""
        assert 'DEV_MODE' not in os.environ
        
        _app_paths = ApplicationPaths("TestApp", forced_dev_mode=True, auto_create=False)

        assert os.environ.get('DEV_MODE') == "True"
    
    def test_path_environment_variables_set(self):
        """Test that path environment variables are set correctly."""
        app_paths = ApplicationPaths("TestApp", forced_os="Linux", auto_create=False)
        
        # Verify all path environment variables are set
        assert os.environ.get('dt_LOGGING_PATH') is not None
        assert os.environ.get('dt_APP_DATA') is not None
        assert os.environ.get('dt_USR_DATA') is not None
        assert os.environ.get('dt_TMP') is not None
        
        # Verify they match the ApplicationPaths attributes
        assert os.environ['dt_LOGGING_PATH'] == app_paths.logging_root_path
        assert os.environ['dt_APP_DATA'] == app_paths.app_data_root_path
        assert os.environ['dt_USR_DATA'] == app_paths.usr_data_root_path
        assert os.environ['dt_TMP'] == app_paths.tmp_root_path


class TestApplicationPathsLogging:
    """Test logging functionality."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()

    def teardown_method(self):
        self.setup_method()
    
    def test_log_paths_method(self):
        """Test the log_paths method outputs correct information."""
        with patch('logging.info') as mock_log:
            app_paths = ApplicationPaths("TestApp", forced_os="Linux", auto_create=False)
            app_paths.log_paths()
            
            # Verify logging.info was called for each path
            assert mock_log.call_count == 4
            
            # Extract the logged messages
            logged_messages = [call.args[0] for call in mock_log.call_args_list]
            
            # Verify each path type was logged
            assert any('Logging Root Path:' in msg for msg in logged_messages)
            assert any('Application Data Root Path:' in msg for msg in logged_messages)
            assert any('User Data Root Path:' in msg for msg in logged_messages)
            assert any('Temp Root Path:' in msg for msg in logged_messages)


class TestApplicationPathsErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()

    def teardown_method(self):
        self.setup_method()
    
    def test_app_data_creation_exception_handling(self):
        """Test handling of exceptions during app data directory creation."""
        with patch('os.getcwd', return_value='/tmp/test'):
            with patch('os.makedirs') as mock_makedirs:
                # The app_data path in dev mode ends with data/app (or data\app on Windows)
                app_data_segment = os.path.join('data', 'app')

                def makedirs_side_effect(path, exist_ok=False):
                    if app_data_segment in path:
                        raise PermissionError("Permission denied")
                    return None

                mock_makedirs.side_effect = makedirs_side_effect

                with patch('logging.warning') as mock_warning:
                    _app_paths = ApplicationPaths("TestApp", forced_dev_mode=True, auto_create=True)

                    # Verify exception was handled and warning was logged
                    warning_messages = [str(call.args[0]) for call in mock_warning.call_args_list]
                    assert any("app_data" in msg and "Permission denied" in msg
                               for msg in warning_messages)
    
    def test_unknown_os_handling(self):
        """Test behavior with unknown operating system uses fallback paths."""
        app_paths = ApplicationPaths("TestApp", forced_os="UnknownOS", auto_create=False)

        # Fallback paths should be set (cwd-based or tempdir-based)
        assert app_paths.logging_root_path is not None
        assert app_paths.app_data_root_path is not None
        assert app_paths.usr_data_root_path is not None
        assert app_paths.tmp_root_path is not None

        # Verify fallback values use cwd or tempdir
        assert 'logs' in app_paths.logging_root_path
        assert 'TestApp' in app_paths.tmp_root_path


class TestApplicationPathsSingleton:
    """Test singleton behaviour of ApplicationPaths."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()

    def teardown_method(self):
        self.setup_method()
    
    def test_singleton_same_parameters(self):
        """Test that same parameters return the same instance."""
        # Note: ApplicationPaths uses singleton decorator, so same parameters should return same instance
        app_paths1 = ApplicationPaths("TestApp", auto_create=False)
        app_paths2 = ApplicationPaths("TestApp", auto_create=False)
        
        # They should be the same instance due to singleton pattern
        assert app_paths1 is app_paths2
    
    def test_singleton_different_parameters(self):
        """Test that different parameters may return different instances based on key."""
        # This depends on how the singleton decorator is configured
        # If no key is specified, it might still be a global singleton
        app_paths1 = ApplicationPaths("TestApp1", auto_create=False)
        app_paths2 = ApplicationPaths("TestApp2", auto_create=False)
        
        # Behavior depends on singleton implementation
        # Document the actual behavior found
        if app_paths1 is app_paths2:
            # Global singleton behavior
            assert app_paths1.app_short_name == app_paths2.app_short_name
        else:
            # Key-based singleton behavior
            assert app_paths1.app_short_name != app_paths2.app_short_name


class TestApplicationPathsGracefulFailure:
    """Test that directory creation failures are handled gracefully."""

    def setup_method(self):
        _clear_singleton_cache()
        _clean_env()

    def teardown_method(self):
        _clear_singleton_cache()
        _clean_env()

    def test_makedirs_permission_error_does_not_propagate(self):
        """Test that PermissionError during makedirs does not crash the application."""
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            # Should NOT raise -- all failures are logged as warnings
            app_paths = ApplicationPaths("TestApp", forced_dev_mode=True, auto_create=True)

            # Path strings must still be set (not None)
            assert app_paths.logging_root_path is not None
            assert app_paths.app_data_root_path is not None
            assert app_paths.usr_data_root_path is not None
            assert app_paths.tmp_root_path is not None

    def test_path_creation_status_reflects_failures(self):
        """Test that path_creation_status records which paths failed."""
        call_count = 0

        def selective_makedirs(path, exist_ok=False):
            """Fail only for paths containing 'app' (app_data)."""
            nonlocal call_count
            call_count += 1
            if os.path.join('data', 'app') in path:
                raise PermissionError("Permission denied")

        with patch('os.makedirs', side_effect=selective_makedirs):
            app_paths = ApplicationPaths("TestApp", forced_dev_mode=True, auto_create=True)

            assert app_paths.path_creation_status['app_data'] is False
            assert app_paths.path_creation_status['tmp'] is True
            assert app_paths.path_creation_status['logging'] is True
            assert app_paths.path_creation_status['usr_data'] is True

    def test_is_path_available_returns_correct_values(self):
        """Test is_path_available convenience method."""
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            app_paths = ApplicationPaths("TestApp", forced_dev_mode=True, auto_create=True)

            assert app_paths.is_path_available('tmp') is False
            assert app_paths.is_path_available('logging') is False
            assert app_paths.is_path_available('usr_data') is False
            assert app_paths.is_path_available('app_data') is False

    def test_is_path_available_none_when_auto_create_disabled(self):
        """Test is_path_available returns None when auto_create was not enabled."""
        app_paths = ApplicationPaths("TestApp", forced_dev_mode=True, auto_create=False)

        assert app_paths.is_path_available('tmp') is None
        assert app_paths.is_path_available('logging') is None
        assert app_paths.is_path_available('app_data') is None

    def test_all_paths_succeed_when_writable(self):
        """Test that all paths are marked as available when creation succeeds."""
        with patch('os.getcwd', return_value=tempfile.mkdtemp()):
            app_paths = ApplicationPaths("TestApp", forced_dev_mode=True, auto_create=True)

            assert app_paths.is_path_available('tmp') is True
            assert app_paths.is_path_available('logging') is True
            assert app_paths.is_path_available('usr_data') is True
            assert app_paths.is_path_available('app_data') is True

    def test_shutil_rmtree_failure_does_not_propagate(self):
        """Test that failure to clean temp directory does not crash."""
        with patch('os.path.exists', return_value=True):
            with patch('shutil.rmtree', side_effect=PermissionError("Permission denied")):
                with patch('os.makedirs'):
                    # Should NOT raise
                    app_paths = ApplicationPaths(
                        "TestApp", forced_dev_mode=True, auto_create=True, clean_temp=True
                    )
                    assert app_paths.tmp_root_path is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
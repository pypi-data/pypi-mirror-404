"""
Tests for container mode functionality.
"""
import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def _clear_singleton(cls):
    """Clear singleton instances by accessing the closure-based dict."""
    if hasattr(cls, '__closure__') and cls.__closure__:
        for cell in cls.__closure__:
            try:
                contents = cell.cell_contents
                if isinstance(contents, dict):
                    contents.clear()
                    return
            except ValueError:
                pass


def _clear_application_paths_singleton():
    """Clear ApplicationPaths singleton instances."""
    from dtPyAppFramework.paths import ApplicationPaths
    _clear_singleton(ApplicationPaths)


def _clear_settings_singleton():
    """Clear Settings singleton instances."""
    from dtPyAppFramework.settings import Settings
    _clear_singleton(Settings)


class TestContainerMode:
    """Test container mode functionality."""

    def setup_method(self, method):
        """Clean up environment before each test."""
        os.environ.pop('CONTAINER_MODE', None)
        os.environ.pop('DEV_MODE', None)
        os.environ.pop('CONTAINER_NAME', None)
        os.environ.pop('POD_NAME', None)
        _clear_application_paths_singleton()

    def teardown_method(self, method):
        """Clean up environment after each test."""
        os.environ.pop('CONTAINER_MODE', None)
        os.environ.pop('DEV_MODE', None)
        os.environ.pop('CONTAINER_NAME', None)
        os.environ.pop('POD_NAME', None)

    def test_container_mode_environment_variable(self):
        """Test that CONTAINER_MODE environment variable is detected."""
        os.environ['CONTAINER_MODE'] = 'true'

        from dtPyAppFramework.paths import ApplicationPaths

        _clear_application_paths_singleton()

        with patch('dtPyAppFramework.paths.os.makedirs'):
            with patch('dtPyAppFramework.paths.shutil.rmtree'):
                app_paths = ApplicationPaths('test-app')

                # Container mode paths should be under current working directory
                assert 'logs' in app_paths.logging_root_path
                assert 'data' in app_paths.app_data_root_path
                assert 'data' in app_paths.usr_data_root_path
                assert 'temp' in app_paths.tmp_root_path

    def test_container_mode_paths(self):
        """Test container mode creates correct directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                os.environ['CONTAINER_MODE'] = 'True'

                # Import after setting environment
                import importlib
                import dtPyAppFramework.paths
                importlib.reload(dtPyAppFramework.paths)
                from dtPyAppFramework.paths import ApplicationPaths

                app_paths = ApplicationPaths('test-container-app')

                # Verify all paths contain the temp directory
                assert temp_dir in app_paths.logging_root_path
                assert temp_dir in app_paths.app_data_root_path
                assert temp_dir in app_paths.usr_data_root_path
                assert temp_dir in app_paths.tmp_root_path

                # Verify paths contain expected directory components
                assert 'logs' in app_paths.logging_root_path
                assert 'data' in app_paths.app_data_root_path
                assert 'data' in app_paths.usr_data_root_path
                assert 'temp' in app_paths.tmp_root_path

                # Verify app and user data point to same directory in container mode
                assert app_paths.app_data_root_path == app_paths.usr_data_root_path

            finally:
                os.chdir(original_cwd)

    def test_container_mode_settings_single_config(self):
        """Test container mode uses single config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                os.environ['CONTAINER_MODE'] = 'True'

                # Create config directory and file
                config_dir = os.path.join(temp_dir, 'config')
                os.makedirs(config_dir, exist_ok=True)
                config_file = os.path.join(config_dir, 'config.yaml')
                with open(config_file, 'w') as f:
                    f.write('test:\n  value: container_config\n')

                # Import and reload after setting up environment
                import importlib
                import dtPyAppFramework.paths
                import dtPyAppFramework.settings
                importlib.reload(dtPyAppFramework.paths)
                importlib.reload(dtPyAppFramework.settings)
                from dtPyAppFramework.paths import ApplicationPaths
                from dtPyAppFramework.settings import Settings

                # Create ApplicationPaths first (required by Settings)
                app_paths = ApplicationPaths('test-container-app')

                settings = Settings(application_paths=app_paths, app_short_name='test-container-app')
                settings.init_settings_readers()

                # Container mode should have only one settings reader
                assert len(settings.settings_readers) == 1

                # Verify it reads from the config directory
                reader = settings.settings_readers[0]
                assert temp_dir in reader.settings_file
                assert 'config' in reader.settings_file

            finally:
                os.chdir(original_cwd)

    def test_standard_mode_vs_container_mode(self):
        """Test difference between standard and container modes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                os.environ['DEV_MODE'] = 'True'

                # Test standard mode first
                os.environ.pop('CONTAINER_MODE', None)
                import importlib
                import dtPyAppFramework.paths
                import dtPyAppFramework.settings
                importlib.reload(dtPyAppFramework.paths)
                importlib.reload(dtPyAppFramework.settings)
                from dtPyAppFramework.paths import ApplicationPaths
                from dtPyAppFramework.settings import Settings

                app_paths_standard = ApplicationPaths('test-app')
                standard_settings = Settings(application_paths=app_paths_standard, app_short_name='test-app')
                standard_settings.init_settings_readers()
                standard_count = len(standard_settings.settings_readers)

                # Clear singletons for container mode test
                _clear_application_paths_singleton()
                _clear_settings_singleton()

                # Test container mode
                os.environ['CONTAINER_MODE'] = 'True'
                importlib.reload(dtPyAppFramework.paths)
                importlib.reload(dtPyAppFramework.settings)
                from dtPyAppFramework.paths import ApplicationPaths as AP2
                from dtPyAppFramework.settings import Settings as ContainerSettings

                app_paths_container = AP2('test-app')
                container_settings = ContainerSettings(application_paths=app_paths_container, app_short_name='test-app')
                container_settings.init_settings_readers()
                container_count = len(container_settings.settings_readers)

                # Standard mode should have more settings readers than container mode
                assert standard_count > container_count
                assert container_count == 1
                assert standard_count >= 3  # working dir + app data + user data

            finally:
                os.chdir(original_cwd)

    def test_container_mode_raw_settings(self):
        """Test container mode raw settings behaviour."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                os.environ['CONTAINER_MODE'] = 'True'

                # Create config directory to make it writable
                config_dir = os.path.join(temp_dir, 'config')
                os.makedirs(config_dir, exist_ok=True)

                import importlib
                import dtPyAppFramework.paths
                import dtPyAppFramework.settings
                importlib.reload(dtPyAppFramework.paths)
                importlib.reload(dtPyAppFramework.settings)
                from dtPyAppFramework.paths import ApplicationPaths
                from dtPyAppFramework.settings import Settings

                app_paths = ApplicationPaths('test-container-app')
                settings = Settings(application_paths=app_paths, app_short_name='test-container-app')
                raw_settings = settings.get_raw_settings()

                # Should have all expected keys
                assert 'app' in raw_settings
                assert 'all_user' in raw_settings
                assert 'current_user' in raw_settings

                # Only 'app' should be writable in container mode
                assert raw_settings['app']['read_only'] == False
                assert raw_settings['all_user']['read_only'] == True
                assert raw_settings['current_user']['read_only'] == True

                # Non-app settings should have container mode message
                assert 'Not available in container mode' in raw_settings['all_user']['raw_data']
                assert 'Not available in container mode' in raw_settings['current_user']['raw_data']

            finally:
                os.chdir(original_cwd)

    def test_abstract_app_container_argument(self):
        """Test that AbstractApp correctly handles container argument."""
        with patch('sys.argv', ['test_app.py', '--container']):
            with patch('dtPyAppFramework.application.ProcessManager'):
                from dtPyAppFramework.application import AbstractApp

                class TestApp(AbstractApp):
                    def define_args(self, arg_parser):
                        pass  # Intentionally empty test fixture
                    def main(self, args):
                        pass  # Intentionally empty test fixture
                    def exiting(self):
                        pass  # Intentionally empty test fixture

                app = TestApp("Test", "1.0", "test", "Test App")

                # The __define_args method uses parse_known_args which parses --container
                # After run() calls __define_args, CONTAINER_MODE should be set
                # We test the argument handling indirectly by calling run()
                # which invokes __define_args internally
                with patch.object(app, 'process_manager', MagicMock()):
                    from argparse import ArgumentParser
                    arg_parser = ArgumentParser(prog='test', description='Test')
                    # Access the private method via name-mangled access
                    app._AbstractApp__define_args(arg_parser)

                assert os.environ.get('CONTAINER_MODE') == 'True'

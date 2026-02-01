"""
Comprehensive tests for ProcessManager multi-processing coordination.

This test suite ensures that ProcessManager correctly handles application initialization,
multi-processing coordination, argument parsing, and service integration across
different operating systems and deployment modes.
"""

import pytest
import os
import sys
import tempfile
import threading
import signal
import time
import platform
from unittest.mock import patch, MagicMock, call, mock_open
from argparse import ArgumentParser

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.process import ProcessManager, is_multiprocess_spawned_instance


def _clear_process_manager_singleton():
    """Clear ProcessManager singleton instances by accessing the closure-based dict."""
    if hasattr(ProcessManager, '__closure__') and ProcessManager.__closure__:
        for cell in ProcessManager.__closure__:
            try:
                contents = cell.cell_contents
                if isinstance(contents, dict):
                    contents.clear()
                    return
            except ValueError:
                pass  # Intentionally empty test fixture


class TestProcessManagerBasic:
    """Test basic ProcessManager functionality and initialization."""

    def setup_method(self):
        """Setup method run before each test."""
        _clear_process_manager_singleton()

    def test_basic_initialization(self):
        """Test basic ProcessManager initialization with required parameters."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        def dummy_exit():
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test Application",
            version="1.0.0",
            short_name="testapp",
            full_name="Test Application",
            console_app=True,
            main_procedure=dummy_main,
            exit_procedure=dummy_exit
        )

        # Verify basic attributes are set
        assert manager.description == "Test Application"
        assert manager.version == "1.0.0"
        assert manager.short_name == "testapp"
        assert manager.full_name == "Test Application"
        assert manager.console_app is True
        assert manager.main_procedure is dummy_main
        assert manager.exit_procedure is dummy_exit

        # Verify initialization state
        assert manager.application_paths is None
        assert manager.application_settings is None
        assert manager.secrets_manager is None
        assert manager.resource_manager is None
        assert manager.log_path is None
        assert manager.multiprocessing_manager is None
        assert manager.stdout_txt_file is None
        assert manager.stderr_txt_file is None
        assert isinstance(manager.running, threading.Event)
        assert manager.spawned_running_event is None

    def test_initialization_without_exit_procedure(self):
        """Test ProcessManager initialization without exit procedure."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=False,
            main_procedure=dummy_main
        )

        assert manager.exit_procedure is None
        assert manager.console_app is False


class TestIsMultiprocessSpawnedInstance:
    """Test the is_multiprocess_spawned_instance helper function."""

    def test_main_process_detection(self):
        """Test detection of main process."""
        with patch('dtPyAppFramework.process.current_process') as mock_process:
            mock_process.return_value.name = "MainProcess"
            with patch('sys.argv', ['script.py']):
                assert is_multiprocess_spawned_instance() is False

    def test_spawned_process_by_name(self):
        """Test detection of spawned process by name."""
        with patch('dtPyAppFramework.process.current_process') as mock_process:
            mock_process.return_value.name = "Process-1"
            assert is_multiprocess_spawned_instance() is True

    def test_spawned_process_by_argv(self):
        """Test detection of spawned process by argv flag."""
        with patch('dtPyAppFramework.process.current_process') as mock_process:
            mock_process.return_value.name = "MainProcess"
            with patch('sys.argv', ['script.py', '--multiprocessing-fork']):
                assert is_multiprocess_spawned_instance() is True


class TestProcessManagerSpawnedInstance:
    """Test ProcessManager functionality in spawned instance mode."""

    def setup_method(self):
        """Setup method run before each test."""
        _clear_process_manager_singleton()

    @patch('dtPyAppFramework.process.is_multiprocess_spawned_instance', return_value=True)
    @patch('dtPyAppFramework.process.paths.ApplicationPaths')
    @patch('dtPyAppFramework.process.settings.Settings')
    @patch('dtPyAppFramework.process.resources.ResourceManager')
    @patch('dtPyAppFramework.process.app_logging.initialise_logging')
    @patch('dtPyAppFramework.app_context.AppContext')
    @patch('builtins.open', mock_open())
    @patch('sys.stdout')
    @patch('sys.stderr')
    @patch('builtins.print')
    @patch('logging.info')
    @patch('logging.exception')
    def test_spawned_application_initialization_success(self, mock_log_exception, mock_log_info,
                                                       mock_print, mock_stderr, mock_stdout,
                                                       mock_app_context,
                                                       mock_logging_init, mock_resource_manager,
                                                       mock_settings, mock_app_paths, mock_is_spawned):
        """Test successful spawned application initialization."""
        # Setup mocks
        mock_app_paths_instance = MagicMock()
        mock_app_paths.return_value = mock_app_paths_instance

        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        mock_resource_manager_instance = MagicMock()
        mock_resource_manager.return_value = mock_resource_manager_instance

        mock_logging_init.return_value = "/tmp/logs"

        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=False,
            main_procedure=dummy_main
        )

        running_event = threading.Event()

        # Test spawned initialization - dunder methods are NOT name-mangled
        manager.__initialise_spawned_application__(
            parent_log_path="/tmp/parent_logs",
            job_id=42,
            worker_id=123,
            job_name="test_job",
            running_event=running_event
        )

        # Verify spawned instance setup
        assert manager.spawned_running_event is running_event
        mock_app_paths.assert_called_once_with(
            app_short_name="testapp",
            spawned_instance=True,
            worker_id=123
        )
        mock_settings.assert_called_once_with(
            application_paths=mock_app_paths_instance,
            app_short_name="testapp"
        )
        mock_resource_manager.assert_called_once_with(application_paths=mock_app_paths_instance)
        mock_logging_init.assert_called_once_with(
            spawned_process=True,
            job_id=42,
            worker_id=123,
            parent_log_path="/tmp/parent_logs"
        )

        # Verify settings initialization
        mock_settings_instance.init_settings_readers.assert_called_once_with()
        mock_settings_instance.secret_manager.load_cloud_stores.assert_called_once()

        # Verify logging and stdout capture
        assert manager.log_path == "/tmp/logs"
        mock_log_info.assert_called()
        mock_print.assert_called()

    @patch('dtPyAppFramework.process.is_multiprocess_spawned_instance', return_value=True)
    @patch('logging.exception')
    def test_spawned_application_initialization_exception(self, mock_log_exception, mock_is_spawned):
        """Test spawned application initialization with exception."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=False,
            main_procedure=dummy_main
        )

        # Mock file objects for cleanup
        manager.stdout_txt_file = MagicMock()
        manager.stderr_txt_file = MagicMock()

        running_event = threading.Event()

        with patch('dtPyAppFramework.process.paths.ApplicationPaths', side_effect=Exception("Test error")):
            manager.__initialise_spawned_application__(
                parent_log_path="/tmp/parent_logs",
                job_id=42,
                worker_id=123,
                job_name="test_job",
                running_event=running_event
            )

        # Verify exception was logged and files were closed
        mock_log_exception.assert_called_once()
        manager.stdout_txt_file.close.assert_called_once()
        manager.stderr_txt_file.close.assert_called_once()


class TestProcessManagerStdoutCapture:
    """Test stdout/stderr capture functionality."""

    def setup_method(self):
        """Setup method run before each test."""
        _clear_process_manager_singleton()

    @patch('builtins.open', mock_open())
    @patch('sys.stdout')
    @patch('sys.stderr')
    def test_stdout_capture_non_console_app(self, mock_stderr, mock_stdout):
        """Test stdout capture for non-console applications."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=False,
            main_procedure=dummy_main
        )

        manager.log_path = "/tmp/logs"
        manager.application_paths = MagicMock()
        manager.application_paths.app_short_name = "testapp"

        manager.__initialise_stdout_capt__()

        # Verify files were opened and sys streams redirected
        assert manager.stdout_txt_file is not None
        assert manager.stderr_txt_file is not None

    def test_stdout_capture_console_app(self):
        """Test that stdout capture is skipped for console applications."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        manager.__initialise_stdout_capt__()

        # Verify no file redirection for console app
        assert manager.stdout_txt_file is None
        assert manager.stderr_txt_file is None


class TestProcessManagerApplicationInitialization:
    """Test main application initialization process."""

    def setup_method(self):
        """Setup method run before each test."""
        _clear_process_manager_singleton()

    @patch('dtPyAppFramework.process.is_multiprocess_spawned_instance', return_value=False)
    @patch('dtPyAppFramework.process.paths.ApplicationPaths')
    @patch('dtPyAppFramework.process.settings.Settings')
    @patch('dtPyAppFramework.process.resources.ResourceManager')
    @patch('dtPyAppFramework.process.app_logging.initialise_logging')
    @patch('dtPyAppFramework.process.MultiProcessingManager')
    @patch('dtPyAppFramework.app_context.AppContext')
    @patch('os.getpid', return_value=12345)
    @patch('builtins.print')
    @patch('logging.info')
    @patch('signal.signal')
    def test_main_application_initialization(self, mock_signal, mock_log_info, mock_print,
                                           mock_getpid, mock_app_context, mock_mp_manager,
                                           mock_logging_init,
                                           mock_resource_manager, mock_settings,
                                           mock_app_paths, mock_is_spawned):
        """Test main application initialization process."""
        # Setup mocks
        mock_app_paths_instance = MagicMock()
        mock_app_paths.return_value = mock_app_paths_instance

        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        mock_resource_manager_instance = MagicMock()
        mock_resource_manager.return_value = mock_resource_manager_instance

        mock_mp_manager_instance = MagicMock()
        mock_mp_manager.return_value = mock_mp_manager_instance

        mock_logging_init.return_value = "/tmp/logs"

        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        # Create mock argument parser
        arg_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.add_secret = False
        mock_args.service = False
        arg_parser.parse_args.return_value = mock_args

        with patch.object(manager, '__main__') as mock_main:
            manager.initialise_application(arg_parser)

        # Verify initialization sequence
        mock_app_paths.assert_called_once_with(app_short_name="testapp")
        mock_settings.assert_called_once_with(application_paths=mock_app_paths_instance)
        mock_settings_instance.init_settings_readers.assert_called_once()
        mock_resource_manager.assert_called_once_with(application_paths=mock_app_paths_instance)
        mock_logging_init.assert_called_once()
        mock_settings_instance.secret_manager.load_cloud_stores.assert_called_once()

        # Verify signal handlers use request_shutdown
        mock_signal.assert_any_call(signal.SIGINT, manager.request_shutdown)
        mock_signal.assert_any_call(signal.SIGTERM, manager.request_shutdown)

        # Verify main was called
        mock_main.assert_called_once_with(mock_args)

    @patch('dtPyAppFramework.process.is_multiprocess_spawned_instance', return_value=False)
    @patch('dtPyAppFramework.process.MultiProcessingManager')
    @patch('dtPyAppFramework.process.paths.ApplicationPaths', side_effect=KeyboardInterrupt())
    @patch('logging.warning')
    def test_keyboard_interrupt_handling(self, mock_log_warning, mock_app_paths,
                                        mock_mp_manager, mock_is_spawned):
        """Test handling of KeyboardInterrupt during initialization."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        arg_parser = MagicMock()

        manager.initialise_application(arg_parser)

        mock_log_warning.assert_called_once_with('(KeyboardInterrupt) Exiting application.')

    @patch('dtPyAppFramework.process.is_multiprocess_spawned_instance', return_value=False)
    @patch('dtPyAppFramework.process.MultiProcessingManager')
    @patch('dtPyAppFramework.process.paths.ApplicationPaths', side_effect=Exception("Test error"))
    @patch('logging.exception')
    def test_general_exception_handling(self, mock_log_exception, mock_app_paths,
                                       mock_mp_manager, mock_is_spawned):
        """Test handling of general exceptions during initialization."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        arg_parser = MagicMock()

        manager.initialise_application(arg_parser)

        mock_log_exception.assert_called_once_with("Test error")


class TestProcessManagerSecretHandling:
    """Test secret management functionality."""

    def setup_method(self):
        """Setup method run before each test."""
        _clear_process_manager_singleton()

    @patch('dtPyAppFramework.process.is_multiprocess_spawned_instance', return_value=False)
    @patch('dtPyAppFramework.process.settings.SecretsManager')
    @patch('dtPyAppFramework.process.settings.Settings')
    @patch('dtPyAppFramework.process.prompt')
    @patch('dtPyAppFramework.process.inquirer')
    @patch('logging.info')
    def test_add_secret_interactive_value(self, mock_log_info, mock_inquirer, mock_prompt,
                                        mock_settings_class, mock_secrets_manager, mock_is_spawned):
        """Test interactive secret addition with value."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        # Setup mocks
        mock_secrets_manager_instance = MagicMock()
        mock_secrets_manager.return_value = mock_secrets_manager_instance

        mock_settings_instance = MagicMock()
        mock_settings_class.return_value = mock_settings_instance

        # Mock interactive prompts
        mock_prompt.return_value = {
            "secret_name": "test_secret",
            "secret_type": "Value"
        }

        mock_secret_inquirer = MagicMock()
        mock_secret_inquirer.execute.return_value = "secret_value_123"
        mock_inquirer.secret.return_value = mock_secret_inquirer

        mock_confirm_inquirer = MagicMock()
        mock_confirm_inquirer.execute.return_value = False  # Don't add another
        mock_inquirer.confirm.return_value = mock_confirm_inquirer

        # Create args for secret addition
        args = MagicMock()
        args.name = None
        args.value = None
        args.file = None

        manager.__add_secret__(args)

        # Verify secret was set
        mock_secrets_manager_instance.set_secret.assert_called_once_with("test_secret", "secret_value_123")
        mock_log_info.assert_called()
        mock_settings_instance.close.assert_called_once()

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data='file_content_123'))
    @patch('dtPyAppFramework.process.settings.SecretsManager')
    @patch('dtPyAppFramework.process.settings.Settings')
    @patch('logging.info')
    @patch('builtins.print')
    def test_add_secret_file_raw(self, mock_print, mock_log_info, mock_settings_class,
                               mock_secrets_manager, mock_exists):
        """Test adding secret from file in raw format."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        # Setup mocks
        mock_secrets_manager_instance = MagicMock()
        mock_secrets_manager.return_value = mock_secrets_manager_instance

        mock_settings_instance = MagicMock()
        mock_settings_class.return_value = mock_settings_instance

        manager._add_secret_file("test_secret", "/path/to/file.txt", "raw")

        # Verify file was read and secret was set
        mock_secrets_manager_instance.set_secret.assert_called_once_with("test_secret", "file_content_123")
        mock_log_info.assert_called()

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data=b'binary_content_123'))
    @patch('base64.b64encode')
    @patch('dtPyAppFramework.process.settings.SecretsManager')
    @patch('dtPyAppFramework.process.settings.Settings')
    @patch('logging.info')
    @patch('builtins.print')
    def test_add_secret_file_base64(self, mock_print, mock_log_info, mock_settings_class,
                                  mock_secrets_manager, mock_b64encode, mock_exists):
        """Test adding secret from file in base64 format."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        # Setup mocks
        mock_secrets_manager_instance = MagicMock()
        mock_secrets_manager.return_value = mock_secrets_manager_instance

        mock_settings_instance = MagicMock()
        mock_settings_class.return_value = mock_settings_instance

        mock_b64encode.return_value.decode.return_value = "YmluYXJ5X2NvbnRlbnRfMTIz"

        manager._add_secret_file("test_secret", "/path/to/file.bin", "base64")

        # Verify file was read as binary and base64 encoded
        mock_secrets_manager_instance.set_secret.assert_called_once_with("test_secret", "YmluYXJ5X2NvbnRlbnRfMTIz")
        mock_log_info.assert_called()

    def test_add_secret_file_not_found(self):
        """Test handling of missing file in secret addition."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        with patch('os.path.exists', return_value=False):
            with patch('builtins.print') as mock_print:
                with pytest.raises(FileNotFoundError):
                    manager._add_secret_file("test_secret", "/nonexistent/file.txt", "raw")

                mock_print.assert_called_with('The file "/nonexistent/file.txt" could not be found.')

    def test_add_secret_file_invalid_store_as(self):
        """Test handling of invalid store_as parameter."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        with patch('os.path.exists', return_value=True):
            with pytest.raises(ValueError) as excinfo:
                manager._add_secret_file("test_secret", "/path/to/file.txt", "invalid")

            assert "Invalid store_as value: invalid" in str(excinfo.value)


class TestProcessManagerServiceHandling:
    """Test Windows service integration."""

    def setup_method(self):
        """Setup method run before each test."""
        _clear_process_manager_singleton()

    @pytest.mark.skipif(platform.system() != 'Windows',
                        reason="call_service is only available on Windows")
    @patch('platform.system', return_value='Windows')
    @patch('dtPyAppFramework.process.call_service')
    @patch('dtPyAppFramework.process.is_multiprocess_spawned_instance', return_value=False)
    @patch('dtPyAppFramework.process.paths.ApplicationPaths')
    @patch('dtPyAppFramework.process.settings.Settings')
    @patch('dtPyAppFramework.process.resources.ResourceManager')
    @patch('dtPyAppFramework.process.app_logging.initialise_logging')
    @patch('dtPyAppFramework.process.MultiProcessingManager')
    @patch('dtPyAppFramework.app_context.AppContext')
    @patch('builtins.open', mock_open())
    @patch('builtins.print')
    @patch('logging.info')
    @patch('sys.argv', ['script.py'])
    def test_windows_service_mode(self, mock_log_info, mock_print,
                                  mock_app_context, mock_mp_manager,
                                  mock_logging_init, mock_resource_manager,
                                  mock_settings, mock_app_paths,
                                  mock_is_spawned, mock_call_service, mock_platform):
        """Test Windows service mode initialization."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        def dummy_exit():
            pass  # Intentionally empty test fixture

        # Setup mocks
        mock_app_paths_instance = MagicMock()
        mock_app_paths.return_value = mock_app_paths_instance

        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        mock_logging_init.return_value = "/tmp/logs"

        manager = ProcessManager(
            description="Test Service",
            version="1.0.0",
            short_name="testsvc",
            full_name="Test Service",
            console_app=False,
            main_procedure=dummy_main,
            exit_procedure=dummy_exit
        )

        arg_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.add_secret = False
        mock_args.service = True
        arg_parser.parse_args.return_value = mock_args

        manager.initialise_application(arg_parser)

        # Verify service was called with correct parameters
        mock_call_service.assert_called_once_with(
            svc_name="testsvc",
            svc_display_name="Test Service",
            svc_description="Test Service",
            main_function=manager.__main__,
            exit_function=manager.call_shutdown
        )

        # Verify sys.argv was reset
        assert sys.argv == ['script.py']


class TestProcessManagerShutdownHandling:
    """Test shutdown and cleanup functionality."""

    def setup_method(self):
        """Setup method run before each test."""
        _clear_process_manager_singleton()

    def test_handle_shutdown_with_exit_procedure(self):
        """Test shutdown handling when exit procedure is provided."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        mock_exit = MagicMock()

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=False,
            main_procedure=dummy_main,
            exit_procedure=mock_exit
        )

        # Mock file objects
        manager.stdout_txt_file = MagicMock()
        manager.stderr_txt_file = MagicMock()

        manager.handle_shutdown()

        # Verify exit procedure was called and files were closed
        mock_exit.assert_called_once()
        manager.stdout_txt_file.close.assert_called_once()
        manager.stderr_txt_file.close.assert_called_once()

    def test_handle_shutdown_console_app(self):
        """Test shutdown handling for console application."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        mock_exit = MagicMock()

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main,
            exit_procedure=mock_exit
        )

        manager.handle_shutdown()

        # Verify exit procedure was called but no file operations for console app
        mock_exit.assert_called_once()
        assert manager.stdout_txt_file is None
        assert manager.stderr_txt_file is None

    def test_call_shutdown(self):
        """Test call_shutdown clears running event."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        # Set running event
        manager.running.set()
        assert manager.running.is_set()

        # Call shutdown
        manager.call_shutdown()

        # Verify running event was cleared
        assert not manager.running.is_set()


class TestProcessManagerMainExecution:
    """Test main execution loop."""

    def setup_method(self):
        """Setup method run before each test."""
        _clear_process_manager_singleton()

    def test_main_execution_loop(self):
        """Test main execution loop with proper shutdown."""
        main_called = False

        def dummy_main(args):
            nonlocal main_called
            main_called = True

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        # Mock dependencies
        with patch.object(manager, 'load_config') as mock_load_config:
            with patch.object(manager, 'handle_shutdown') as mock_handle_shutdown:
                with patch('logging.info') as mock_log_info:
                    with patch('logging.debug'):
                        args = MagicMock()
                        manager.__main__(args)

        # Verify execution sequence
        assert main_called
        mock_load_config.assert_called_once()
        mock_handle_shutdown.assert_called_once()
        mock_log_info.assert_called()


class TestProcessManagerLoadConfig:
    """Test configuration loading functionality."""

    def setup_method(self):
        """Setup method run before each test."""
        _clear_process_manager_singleton()

    @patch('dtPyAppFramework.process.is_multiprocess_spawned_instance', return_value=False)
    def test_load_config_main_process(self, mock_is_spawned):
        """Test config loading in main process."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        # Mock application paths
        mock_app_paths = MagicMock()
        manager.application_paths = mock_app_paths

        manager.load_config()

        # Verify log_paths was called for main process
        mock_app_paths.log_paths.assert_called_once()

    @patch('dtPyAppFramework.process.is_multiprocess_spawned_instance', return_value=True)
    def test_load_config_spawned_process(self, mock_is_spawned):
        """Test config loading in spawned process."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        # Mock application paths
        mock_app_paths = MagicMock()
        manager.application_paths = mock_app_paths

        manager.load_config()

        # Verify log_paths was not called for spawned process
        mock_app_paths.log_paths.assert_not_called()


class TestProcessManagerSingleton:
    """Test singleton behavior of ProcessManager."""

    def setup_method(self):
        """Setup method run before each test."""
        _clear_process_manager_singleton()

    def test_singleton_same_parameters(self):
        """Test that same parameters return the same instance."""
        def dummy_main(args):
            pass  # Intentionally empty test fixture

        manager1 = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        manager2 = ProcessManager(
            description="Test App",
            version="1.0.0",
            short_name="testapp",
            full_name="Test App",
            console_app=True,
            main_procedure=dummy_main
        )

        # They should be the same instance due to singleton pattern
        assert manager1 is manager2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Tests for the AppContext singleton facade.

Verifies that AppContext correctly delegates to the underlying framework
singletons (ApplicationPaths, Settings, SecretsManager, ResourceManager)
and exposes application metadata.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.app_context import AppContext


def _clear_singleton_cache():
    """Clear the singleton instance cache for AppContext."""
    if hasattr(AppContext, '__closure__') and AppContext.__closure__:
        for cell in AppContext.__closure__:
            try:
                contents = cell.cell_contents
                if isinstance(contents, dict):
                    contents.clear()
                    return
            except ValueError:
                continue


class TestAppContextSingleton:
    """Test singleton behaviour of AppContext."""

    def setup_method(self):
        _clear_singleton_cache()

    def teardown_method(self):
        _clear_singleton_cache()

    def test_singleton_returns_same_instance(self):
        """Two calls to AppContext() return the same instance."""
        ctx1 = AppContext(version="1.0", full_name="App", short_name="app", description="Desc")
        ctx2 = AppContext()
        assert ctx1 is ctx2

    def test_first_call_metadata_preserved(self):
        """Arguments from the first call are preserved on subsequent calls."""
        _ctx1 = AppContext(version="2.0", full_name="Full", short_name="short", description="D")
        ctx2 = AppContext(version="IGNORED", full_name="IGNORED", short_name="IGNORED", description="IGNORED")
        assert ctx2.version == "2.0"
        assert ctx2.full_name == "Full"
        assert ctx2.short_name == "short"
        assert ctx2.description == "D"


class TestAppContextMetadata:
    """Test application metadata properties."""

    def setup_method(self):
        _clear_singleton_cache()

    def teardown_method(self):
        _clear_singleton_cache()

    def test_version_property(self):
        ctx = AppContext(version="3.1.0", full_name="My App", short_name="myapp", description="A test app")
        assert ctx.version == "3.1.0"

    def test_full_name_property(self):
        ctx = AppContext(version="1.0", full_name="My Full Name", short_name="mfn", description="Desc")
        assert ctx.full_name == "My Full Name"

    def test_short_name_property(self):
        ctx = AppContext(version="1.0", full_name="App", short_name="testshort", description="Desc")
        assert ctx.short_name == "testshort"

    def test_description_property(self):
        ctx = AppContext(version="1.0", full_name="App", short_name="app", description="A detailed description")
        assert ctx.description == "A detailed description"

    def test_defaults_are_none(self):
        ctx = AppContext()
        assert ctx.version is None
        assert ctx.full_name is None
        assert ctx.short_name is None
        assert ctx.description is None


class TestAppContextPaths:
    """Test path properties delegate to ApplicationPaths."""

    def setup_method(self):
        _clear_singleton_cache()

    def teardown_method(self):
        _clear_singleton_cache()

    @patch('dtPyAppFramework.app_context.ApplicationPaths', create=True)
    def test_logging_path(self, _mock_cls):
        """logging_path delegates to ApplicationPaths().logging_root_path."""
        mock_paths = MagicMock()
        mock_paths.logging_root_path = '/var/log/testapp'

        with patch('dtPyAppFramework.paths.ApplicationPaths', return_value=mock_paths):
            ctx = AppContext(version="1.0", full_name="T", short_name="t", description="")
            assert ctx.logging_path == '/var/log/testapp'

    @patch('dtPyAppFramework.app_context.ApplicationPaths', create=True)
    def test_app_data_path(self, _mock_cls):
        mock_paths = MagicMock()
        mock_paths.app_data_root_path = '/var/lib/testapp'

        with patch('dtPyAppFramework.paths.ApplicationPaths', return_value=mock_paths):
            ctx = AppContext(version="1.0", full_name="T", short_name="t", description="")
            assert ctx.app_data_path == '/var/lib/testapp'

    @patch('dtPyAppFramework.app_context.ApplicationPaths', create=True)
    def test_usr_data_path(self, _mock_cls):
        mock_paths = MagicMock()
        mock_paths.usr_data_root_path = '/home/user/.local/share/testapp'

        with patch('dtPyAppFramework.paths.ApplicationPaths', return_value=mock_paths):
            ctx = AppContext(version="1.0", full_name="T", short_name="t", description="")
            assert ctx.usr_data_path == '/home/user/.local/share/testapp'

    @patch('dtPyAppFramework.app_context.ApplicationPaths', create=True)
    def test_tmp_path(self, _mock_cls):
        mock_paths = MagicMock()
        mock_paths.tmp_root_path = '/tmp/testapp'

        with patch('dtPyAppFramework.paths.ApplicationPaths', return_value=mock_paths):
            ctx = AppContext(version="1.0", full_name="T", short_name="t", description="")
            assert ctx.tmp_path == '/tmp/testapp'


class TestAppContextConfigPaths:
    """Test config_file_paths property."""

    def setup_method(self):
        _clear_singleton_cache()

    def teardown_method(self):
        _clear_singleton_cache()

    def test_config_file_paths_returns_reader_paths(self):
        """config_file_paths returns settings_file from each reader."""
        reader1 = MagicMock()
        reader1.settings_file = '/etc/testapp/config.yaml'
        reader2 = MagicMock()
        reader2.settings_file = '/home/user/.config/testapp/config.yaml'

        mock_settings = MagicMock()
        mock_settings.settings_readers = [reader1, reader2]

        with patch('dtPyAppFramework.settings.Settings', return_value=mock_settings):
            ctx = AppContext(version="1.0", full_name="T", short_name="t", description="")
            paths = ctx.config_file_paths
            assert paths == ['/etc/testapp/config.yaml', '/home/user/.config/testapp/config.yaml']

    def test_config_file_paths_empty_when_no_readers(self):
        mock_settings = MagicMock()
        mock_settings.settings_readers = []

        with patch('dtPyAppFramework.settings.Settings', return_value=mock_settings):
            ctx = AppContext()
            assert ctx.config_file_paths == []


class TestAppContextSettings:
    """Test settings convenience methods."""

    def setup_method(self):
        _clear_singleton_cache()

    def teardown_method(self):
        _clear_singleton_cache()

    def test_get_setting_delegates(self):
        mock_settings = MagicMock()
        mock_settings.get.return_value = 'test_value'

        with patch('dtPyAppFramework.settings.Settings', return_value=mock_settings):
            ctx = AppContext(version="1.0", full_name="T", short_name="t", description="")
            result = ctx.get_setting('app.name', 'default')
            mock_settings.get.assert_called_once_with('app.name', 'default')
            assert result == 'test_value'

    def test_get_setting_default(self):
        mock_settings = MagicMock()
        mock_settings.get.return_value = None

        with patch('dtPyAppFramework.settings.Settings', return_value=mock_settings):
            ctx = AppContext()
            _result = ctx.get_setting('missing.key')
            mock_settings.get.assert_called_once_with('missing.key', None)

    def test_set_setting_delegates(self):
        mock_settings = MagicMock()

        with patch('dtPyAppFramework.settings.Settings', return_value=mock_settings):
            ctx = AppContext()
            ctx.set_setting('app.timeout', 60, 'User_Local_Store')
            mock_settings.set.assert_called_once_with('app.timeout', 60, 'User_Local_Store')


class TestAppContextSecrets:
    """Test secrets convenience methods."""

    def setup_method(self):
        _clear_singleton_cache()

    def teardown_method(self):
        _clear_singleton_cache()

    def test_get_secret_delegates(self):
        mock_secret_manager = MagicMock()
        mock_secret_manager.get_secret.return_value = 'secret_value'
        mock_settings = MagicMock()
        mock_settings.secret_manager = mock_secret_manager

        with patch('dtPyAppFramework.settings.Settings', return_value=mock_settings):
            ctx = AppContext()
            result = ctx.get_secret('api_key', 'fallback', 'User_Local_Store')
            mock_secret_manager.get_secret.assert_called_once_with('api_key', 'fallback', 'User_Local_Store')
            assert result == 'secret_value'

    def test_set_secret_delegates(self):
        mock_secret_manager = MagicMock()
        mock_settings = MagicMock()
        mock_settings.secret_manager = mock_secret_manager

        with patch('dtPyAppFramework.settings.Settings', return_value=mock_settings):
            ctx = AppContext()
            ctx.set_secret('db_password', 'new_pass')
            mock_secret_manager.set_secret.assert_called_once_with('db_password', 'new_pass', 'User_Local_Store')

    def test_delete_secret_delegates(self):
        mock_secret_manager = MagicMock()
        mock_settings = MagicMock()
        mock_settings.secret_manager = mock_secret_manager

        with patch('dtPyAppFramework.settings.Settings', return_value=mock_settings):
            ctx = AppContext()
            ctx.delete_secret('old_key', 'App_Local_Store')
            mock_secret_manager.delete_secret.assert_called_once_with('old_key', 'App_Local_Store')


class TestAppContextResources:
    """Test resource convenience method."""

    def setup_method(self):
        _clear_singleton_cache()

    def teardown_method(self):
        _clear_singleton_cache()

    def test_get_resource_path_delegates(self):
        mock_resource_manager = MagicMock()
        mock_resource_manager.get_resource_path.return_value = '/usr/share/testapp/template.yaml'

        with patch('dtPyAppFramework.resources.ResourceManager', return_value=mock_resource_manager):
            ctx = AppContext()
            result = ctx.get_resource_path('template.yaml')
            mock_resource_manager.get_resource_path.assert_called_once_with('template.yaml')
            assert result == '/usr/share/testapp/template.yaml'

    def test_get_resource_path_not_found(self):
        mock_resource_manager = MagicMock()
        mock_resource_manager.get_resource_path.return_value = None

        with patch('dtPyAppFramework.resources.ResourceManager', return_value=mock_resource_manager):
            ctx = AppContext()
            result = ctx.get_resource_path('nonexistent.txt')
            assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

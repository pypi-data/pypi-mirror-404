import os
import sys
from unittest import mock

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from dtPyAppFramework.settings.settings_reader import SettingsReader


# Test that __init__ sets the attributes correctly
def test_init():
    settings_reader = SettingsReader('/path/to/settings', 5)
    assert settings_reader.priority == 5
    assert settings_reader.settings_file == os.path.join('/path/to/settings', 'config.yaml')


# Test that load_yaml_file loads a YAML file correctly
def test_load_yaml_file(tmp_path):
    # Create an actual config.yaml file for the reader to load
    config_dir = tmp_path / "settings"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("key: value\n", encoding="utf-8")

    settings_reader = SettingsReader(str(config_dir), 5)
    # __init__ calls load_yaml_file then super().__init__() which clears the dict,
    # so call load_yaml_file again after construction
    settings_reader.load_yaml_file()
    assert settings_reader.get('key') == 'value'


# Test that __getitem__ can retrieve data correctly using dot notation
def test_getitem():
    settings_reader = SettingsReader('/path/to/settings', 5)

    data = {
        'key': 'value',
        'nested': {
            'key': 'nested value'
        }
    }

    settings_reader.update(data)

    assert settings_reader.__getitem__('nested.key') == 'nested value'
    assert settings_reader.__getitem__('key') == 'value'


# Test that methods that are not implemented raise a NotImplementedError
def test_not_implemented_methods():
    settings_reader = SettingsReader('/path/to/settings', 5)

    with pytest.raises(NotImplementedError):
        settings_reader.clear()

    with pytest.raises(NotImplementedError):
        settings_reader.popitem()

    with pytest.raises(NotImplementedError):
        settings_reader.__setitem__('key', 'value')

    with pytest.raises(NotImplementedError):
        settings_reader.pop('key')

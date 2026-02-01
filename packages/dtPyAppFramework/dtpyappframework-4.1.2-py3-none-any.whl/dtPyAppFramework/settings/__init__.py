import logging
from typing import Optional

from ..paths import ApplicationPaths
from ..decorators import singleton
from .settings_reader import SettingsReader
from .secrets import SecretsManager

import os


@singleton()
class Settings(dict):
    """
    Singleton class for managing application settings.

    Attributes:
        application_paths (ApplicationPaths): Object managing application paths.
        app_short_name (str): Short name of the application.
        settings_readers (list): List of settings readers.
        persistent_settings_stores (list): List of persistent settings stores.
        secret_manager (SecretsManager): Manager for handling secrets.
    """

    def __init__(self, application_paths=None, app_short_name=None) -> None:
        """
        Initialize Settings.

        Args:
            application_paths (ApplicationPaths, optional): Object managing application paths.
            app_short_name (str, optional): Short name of the application.
        """
        self.application_paths = application_paths
        self.app_short_name = app_short_name
        if not self.application_paths:
            self.application_paths = ApplicationPaths()

        self.settings_readers = []
        self.persistent_settings_stores = []
        self.secret_manager: Optional[SecretsManager] = None
        self.cloud_session_manager = None

        super().__init__()

    def close(self):
        self.secret_manager.close()

    def init_settings_readers(self):
        """
        Initialize settings readers.
        """
        if os.environ.get("CONTAINER_MODE", None):
            # Container mode: single config directory only
            self.settings_readers.append(SettingsReader(os.path.join(os.getcwd(), "config"), 300))
        else:
            # Standard layered configuration
            self.settings_readers.append(SettingsReader(os.path.join(os.getcwd(), "config"), 300))
            self.settings_readers.append(SettingsReader(self.application_paths.app_data_root_path, 200))
            self.settings_readers.append(SettingsReader(self.application_paths.usr_data_root_path, 100))

        self.settings_readers.sort(key=lambda x: x.priority)

        from ..cloud import CloudSessionManager
        self.cloud_session_manager = CloudSessionManager()
        self.secret_manager = SecretsManager(application_paths=self.application_paths, application_settings=self,
                                             cloud_session_manager=self.cloud_session_manager)

    def persist_settings(self, settings, scope):
        if os.environ.get("CONTAINER_MODE", None):
            # Container mode: all settings go to single config directory
            p = os.path.join(os.getcwd(), "config")
        else:
            # Standard mode: use appropriate scope directories
            if scope == 'app':
                p = os.path.join(os.getcwd(), "config")
            elif scope == 'all_user':
                p = self.application_paths.app_data_root_path
            elif scope == 'current_user':
                p = self.application_paths.usr_data_root_path
            else:
                raise ValueError(f'The Settings Scope "{scope}" is not recognised.')

        p = os.path.join(p, 'config.yaml')
        with open(p, 'w') as i_set:
            i_set.write(settings)

    def get_raw_settings(self):
        raw_settings = {}

        if os.environ.get("CONTAINER_MODE", None):
            # Container mode: only single config file
            keys_to_process = ['app']
        else:
            # Standard mode: all layered configs
            keys_to_process = ['app', 'all_user', 'current_user']

        for key in keys_to_process:
            raw_settings[key] = {'read_only': False, 'raw_data': ''}

            p = None
            if key == 'app' or os.environ.get("CONTAINER_MODE", None):
                p = os.path.join(os.getcwd(), "config")
            elif key == 'all_user':
                p = self.application_paths.app_data_root_path
            elif key == 'current_user':
                p = self.application_paths.usr_data_root_path

            p = os.path.join(p, 'config.yaml')
            if os.path.exists(p):
                with open(p, 'r') as i_set:
                    raw_settings[key]['raw_data'] = i_set.read()

            try:
                with open(p, 'w') as o_set:
                    o_set.write(raw_settings[key]['raw_data'])
                raw_settings[key]['read_only'] = False
            except Exception as ex:
                logging.error(str(ex))
                raw_settings[key]['read_only'] = True

        # In container mode, also populate empty entries for UI compatibility
        if os.environ.get("CONTAINER_MODE", None):
            for key in ['all_user', 'current_user']:
                raw_settings[key] = {'read_only': True, 'raw_data': '# Not available in container mode'}

        return raw_settings

    def get_requests_tor_proxy(self) -> dict:
        """
        Gets TOR Proxy configuration in a format compatible with Requests.

        Returns:
            dict: Dictionary of HTTP and HTTPS configuration for TOR Proxy.
        """
        proxy = self.get('settings.proxies.tor_proxy', '127.0.0.1:9150')
        return {"http": 'socks5h://' + proxy,
                "https": 'socks5h://' + proxy}

    def get_selenium_tor_proxy(self) -> str:
        """
        Gets TOR Proxy configuration in a format compatible with Selenium.

        Returns:
            str: String value for proxy configuration.
        """
        proxy = self.get('settings.proxies.tor_proxy', '127.0.0.1:9150')
        return '--proxy-server=socks5://' + proxy

    def get(self, key, default=None):
        """
        Get the value of a setting.

        Args:
            key (str): Key of the setting.
            default: Default value if the setting is not found.

        Returns:
            Value of the setting or the default value.
        """
        try:
            value = self.__getitem__(key)
            value = self._replace_value(value)
            if not value:
                return default
            return value
        except KeyError:
            return default

    def _replace_value(self, obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    obj[key] = self._lookup_alias_value(value)
                elif isinstance(value, (dict, list)):
                    self._replace_value(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    obj[i] = self._lookup_alias_value(item)
                elif isinstance(item, (dict, list)):
                    self._replace_value(item)
        elif isinstance(obj, str):
            obj = self._lookup_alias_value(obj)

        return obj

    def _lookup_alias_value(self, value):
        if isinstance(value, str) and str(value).startswith('ENV/'):
            env_key = str(value).replace('ENV/', '').strip()
            if env_key:  # Only lookup if key is not empty
                return os.getenv(env_key, value)
            return value
        if isinstance(value, str) and str(value).startswith('SEC/'):
            secret_key = str(value).replace('SEC/', '').strip()
            if secret_key:  # Only lookup if key is not empty
                return self.secret_manager.get_secret(secret_key, None)
            return None  # Return None for empty secret key references
        if isinstance(value, str) and str(value).startswith('<USR>'):
            return str(value).replace('<USR>', self.application_paths.usr_data_root_path).strip()
        if isinstance(value, str) and str(value).startswith('<APP>'):
            return str(value).replace('<APP>', self.application_paths.app_data_root_path).strip()
        return value

    def set(self, key, value, store_name=None):
        """
        Set the value of a setting.

        Args:
            key (str): Key of the setting.
            value: Value to set.
            store_name (str, optional): Name of the store for persistent settings.
        """
        self.secret_manager.set_persistent_setting(key, value)

    def __getattr__(self, key):
        """
        Get attribute based on key.

        Args:
            key (str): Key of the attribute.

        Returns:
            Value of the attribute.

        Raises:
            AttributeError: If the attribute is not found.
        """
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError("object has no attribute '%s'" % key)

    def __setitem__(self, key, value):
        """
        Set item in the dictionary.

        Args:
            key (str): Key of the item.
            value: Value to set.
        """
        # If the value of a setting is changed or new setting added,
        # then it will add it to the persistent store and will override any settings in the config YAML.
        return self.set(key=key, value=value)

    def __getitem__(self, key):
        """
        Get item from the dictionary.

        Args:
            key (str): Key of the item.

        Returns:
            Value of the item.
        """
        # Validate key is not empty
        if not key or (isinstance(key, str) and not key.strip()):
            return None

        if self.secret_manager is not None:
            persistent_value = self.secret_manager.get_secret(key)
            if persistent_value:
                return persistent_value

        value = None
        for reader in self.settings_readers:
            try:
                value = reader.__getitem__(key)
            except Exception:
                value = None
            if value:
                break

        return value

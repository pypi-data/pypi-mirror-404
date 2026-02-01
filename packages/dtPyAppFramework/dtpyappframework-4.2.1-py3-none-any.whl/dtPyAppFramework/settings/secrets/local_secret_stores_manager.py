from ...paths import ApplicationPaths
from .local_secret_store import LocalSecretStore
import logging


class LocalSecretStoresManager:
    """
    Manages local secret stores with direct access.

    Each process (main or spawned) creates its own instance and accesses
    keystore files directly. Cross-process synchronisation is handled by
    FileLock in PasswordProtectedKeystoreWithHMAC.
    """

    def __init__(self, application_paths=None, application_settings=None):
        self.application_paths = application_paths
        self.application_settings = application_settings
        self.stores = []
        self.store_names = []
        self._load_stores()

    def _load_stores(self):
        if not self.application_paths:
            self.application_paths = ApplicationPaths()

        self.stores.append(LocalSecretStore(store_name="User_Local_Store",
                                            store_priority=0,
                                            root_store_path=self.application_paths.usr_data_root_path,
                                            application_settings=self.application_settings,
                                            app_short_name=self.application_paths.app_short_name))

        try:
            self.stores.append(LocalSecretStore(store_name="App_Local_Store",
                                                store_priority=1,
                                                root_store_path=self.application_paths.app_data_root_path,
                                                application_settings=self.application_settings,
                                                app_short_name=self.application_paths.app_short_name))
        except Exception as ex:
            logging.warning(f'Skipping APP Local Secret Store: {ex}')

        for store in self.stores:
            self.store_names.append(store.store_name)

    def close(self):
        """Close the local secret stores manager. No cleanup required with direct access."""
        pass

    def _get_store(self, store_name):
        """
        Get a secret store by name.

        Args:
            store_name (str): Name of the secret store.

        Returns:
            Secret store instance if found, else None.
        """
        for store in self.stores:
            if store_name == store.store_name:
                return store
        return None

    def get_local_stores_index(self):
        _index = {"User_Local_Store": {}, "App_Local_Store": {}}
        for key in _index:
            try:
                _index[key]['available'] = self.store_available(key)
                _index[key]['index'] = self.get_index(key)
                _index[key]['read_only'] = self.store_read_only(key)
            except Exception as ex:
                logging.error(str(ex))
                _index[key]['available'] = False

        return _index

    def store_available(self, store_name):
        store = self._get_store(store_name)
        if store is None:
            return False
        return store.store_available

    def get_index(self, store_name):
        store = self._get_store(store_name)
        if store is None:
            return []
        return store.get_index()

    def store_read_only(self, store_name):
        store = self._get_store(store_name)
        if store is None:
            return True
        return store.store_read_only

    def _parse_store_qualified_key(self, key, store_name=None):
        """
        Parse a dotted key into its store name and secret key components.

        If the key is in the format 'StoreName.SecretKey' and the store name
        matches a known store, the key is split accordingly.

        Args:
            key (str): The secret key, potentially store-qualified.
            store_name (str): An existing store name override, if provided.

        Returns:
            tuple: A (key, store_name) pair with the parsed values.
        """
        parts = key.split(".")
        if len(parts) == 2 and parts[0] in self.store_names:
            return parts[1], parts[0]
        return key, store_name

    def _lookup_in_stores(self, key, store_name=None):
        """
        Look up a secret across local secret stores.

        If a specific store_name is provided, only that store is queried.
        Otherwise, all available local stores are searched in priority order.

        Args:
            key (str): The secret key to retrieve.
            store_name (str): Optional store name to restrict the lookup.

        Returns:
            The secret value if found, else None.
        """
        for store in self.stores:
            if store_name and store_name == store.store_name:
                if store.store_available:
                    return store.get_secret(key, None)
                logging.error(f'Store {store.store_name} is not available to retrieve secret.')
                return None
            elif not store_name and store.store_available:
                value = store.get_secret(key, None)
                if value:
                    return value
        return None

    def get_secret(self, key, default_value=None, store_name=None):
        """
        Retrieve a secret from the local stores.

        Args:
            key (str): Key of the secret.
            default_value: Default value to return if the secret is not found.
            store_name (str): Optional store name to restrict the lookup.

        Returns:
            Secret value if found, else default_value.
        """
        # Defensive check for empty keys
        if not key or (isinstance(key, str) and not key.strip()):
            logging.debug('Empty key passed to get_secret, returning default value')
            return default_value

        key, store_name = self._parse_store_qualified_key(key, store_name)
        value = self._lookup_in_stores(key, store_name)

        if not value:
            logging.debug(f'The Secret {key} was not found. Returning default value.')
            value = default_value

        return value

    def set_persistent_setting(self, key, value):
        for store in self.stores:
            if 'User_Local_Store' == store.store_name:
                if store.store_available and not store.store_read_only:
                    store.set_persistent_setting(key, value)
                else:
                    logging.warning(f'Secrets Store {store.store_name} is either not available or is read only.')
                break

    def set_secret(self, key, value, store_name='User_Local_Store'):
        if not store_name:
            store_name = 'User_Local_Store'
        for store in self.stores:
            if store_name == store.store_name:
                if store.store_available and not store.store_read_only:
                    store.set_secret(key, value)
                else:
                    logging.warning(f'Secrets Store {store.store_name} is either not available or is read only.')
                break

    def delete_secret(self, key, store_name='User_Local_Store'):
        for store in self.stores:
            if store_name and store_name == store.store_name:
                store.delete_secret(key)
                break

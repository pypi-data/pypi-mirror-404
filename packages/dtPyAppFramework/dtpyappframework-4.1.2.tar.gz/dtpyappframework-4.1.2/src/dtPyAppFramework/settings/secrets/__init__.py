import logging
from ...paths import ApplicationPaths
from ...decorators import singleton
from .local_secret_store import LocalSecretStore
from .aws_secret_store import AWSSecretsStore
from .azure_secret_store import AzureSecretsStore
from .local_secret_stores_manager import LocalSecretStoresManager


@singleton()
class SecretsManager(object):
    """
    A singleton class responsible for managing secrets across different secret stores.

    Attributes:
        application_paths (ApplicationPaths): An instance of ApplicationPaths providing paths for secret stores.
        application_settings (Settings): An instance of Settings providing application settings.
        stores (list): A list to hold different secret stores.
    """

    def __init__(self, application_paths=None, application_settings=None, cloud_session_manager=None) -> None:
        """
        Initialize the SecretsManager.

        Args:
            application_paths (ApplicationPaths): An instance of ApplicationPaths providing paths for secret stores.
            application_settings (Settings): An instance of Settings providing application settings.
        """
        super().__init__()
        self.application_paths = application_paths
        self.application_settings = application_settings
        self.cloud_session_manager = cloud_session_manager
        self.stores = []
        self.store_names = []

        if not self.application_paths:
            self.application_paths = ApplicationPaths()

        self.local_secrets_store_manager = LocalSecretStoresManager(application_paths, application_settings)
        self.store_names.extend(self.local_secrets_store_manager.store_names)


    def close(self):
        self.local_secrets_store_manager.close()

    def get_local_stores_index(self):
        return self.local_secrets_store_manager.get_local_stores_index()

    def _sort_stores(self):
        self.stores.sort(key=lambda x: x.store_priority)
        for store in self.stores:
            self.store_names.append(store.store_name)

    def load_cloud_stores(self):
        """
        Load cloud secret stores based on settings.
        """
        if self.application_settings.get('secrets_manager', None) and self.application_settings.get(
                'secrets_manager.cloud_stores', None):
            for store_name in self.application_settings.get('secrets_manager.cloud_stores'):
                # Add AWS secret store
                if self.application_settings.get(f'secrets_manager.cloud_stores.{store_name}.store_type') == 'aws':
                    self.stores.append(AWSSecretsStore(store_priority=self.application_settings.get(
                        f'secrets_manager.cloud_stores.{store_name}.priority'),
                                                       store_name=store_name,
                        cloud_session_manager=self.cloud_session_manager,
                                                       application_settings=self.application_settings,
                    ))

                # Add Azure secret store
                if self.application_settings.get(f'secrets_manager.cloud_stores.{store_name}.store_type') == 'azure':
                    self.stores.append(AzureSecretsStore(store_priority=self.application_settings.get(
                        f'secrets_manager.cloud_stores.{store_name}.priority'),
                                                         store_name=store_name,
                        cloud_session_manager=self.cloud_session_manager,
                                                         application_settings=self.application_settings))

        # Sort stores based on priority
        self._sort_stores()

    def get_store(self, store_name):
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

    def _lookup_cloud_store(self, key, store_name=None):
        """
        Look up a secret across cloud secret stores.

        If a specific store_name is provided, only that store is queried.
        Otherwise, all available cloud stores are searched in priority order.

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
        Get a secret from the secret stores.

        Args:
            key (str): Key of the secret.
            default_value: Default value to return if the secret is not found.
            store_name (str): Name of the secret store.

        Returns:
            Secret value if found, else default_value.
        """
        # Defensive check for empty keys
        if not key or (isinstance(key, str) and not key.strip()):
            logging.debug('Empty key passed to get_secret, returning default value')
            return default_value

        key, store_name = self._parse_store_qualified_key(key, store_name)

        value = None
        if store_name is None or store_name in ['User_Local_Store', 'App_Local_Store']:
            value = self.local_secrets_store_manager.get_secret(key, value, store_name)

        if not value:
            value = self._lookup_cloud_store(key, store_name)

        if not value:
            logging.debug(f'The Secret {key} was not found. Returning default value.')
            value = default_value

        return value

    def set_persistent_setting(self, key, value):
        self.local_secrets_store_manager.set_persistent_setting(key, value)

    def set_secret(self, key, value, store_name='User_Local_Store'):
        """
        Set a secret in the specified secret store.

        Args:
            key (str): Key of the secret.
            value: Value of the secret.
            store_name (str): Name of the secret store (default is 'User_Local_Store').
        """
        if not store_name:
            store_name = 'User_Local_Store'

        if store_name in ['User_Local_Store', 'App_Local_Store']:
            return self.local_secrets_store_manager.set_secret(key, value, store_name)

        for store in self.stores:
            if store_name == store.store_name:
                if store.store_available and not store.store_read_only:
                    store.set_secret(key, value)
                else:
                    logging.warning(f'Secrets Store {store.store_name} is either not available or is read only.')
                break

    def delete_secret(self, key, store_name='User_Local_Store'):
        """
        Delete a secret from the specified secret store.

        Args:
            key (str): Key of the secret.
            store_name (str): Name of the secret store (default is 'User_Local_Store').

        Returns:
            True if the secret is deleted, else False.
        """
        for store in self.stores:
            if store_name and store_name == store.name():
                store.delete_secret(key)
                break

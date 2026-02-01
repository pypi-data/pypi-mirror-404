from .secret_store import AbstractSecretStore, SecretsStoreException
from shutil import which
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, CertificateCredential, ClientSecretCredential, InteractiveBrowserCredential
import logging


class AzureSecretsStore(AbstractSecretStore):
    """
    A class representing an Azure Secrets Store for managing secrets.

    Attributes:
        store_priority (int): Priority of the secret store.
        store_name (str): Name of the secret store.
        application_settings (Settings): An instance of Settings providing application settings.
        azure_keyvault (str): Azure KeyVault URL.
        azure_identity_type (str): Type of Azure identity to use (certificate, key, interactive_browser).
        azure_tenant_id (str): Azure Tenant ID.
        azure_client (SecretClient): Azure SecretClient for interacting with Azure KeyVault.
        kv_uri (str): Azure KeyVault URI.

    Methods:
        get_secret(key, default_value=None): Retrieve a secret from Azure KeyVault.
        set_secret(key, value): Set a secret in Azure KeyVault.
        delete_secret(key): Delete a secret from Azure KeyVault.
    """

    def __init__(self, store_priority, store_name, application_settings, cloud_session_manager) -> None:
        """
        Initialize the AzureSecretsStore.

        Args:
            store_priority (int): Priority of the secret store.
            store_name (str): Name of the secret store.
            application_settings (Settings): An instance of Settings providing application settings.
        """
        super().__init__(store_name, "Azure_Secrets_Store", store_priority, application_settings)
        self.cloud_session_manager = cloud_session_manager

        # Get Azure KeyVault URL
        self.azure_keyvault = self.get_store_setting('azure_keyvault')
        if not self.azure_keyvault:
            raise SecretsStoreException('Azure KeyVault Store is missing required azure_keyvault parameter.')

        # Get Azure identity type
        self.session_name = self.get_store_setting('session_name')
        if not self.session_name:
            raise SecretsStoreException('Azure KeyVault Store is missing required session_name parameter.')

        credential = self.cloud_session_manager.get_session(self.session_name)

        if not credential:
            raise SecretsStoreException(f'Azure KeyVault Store does not have a valid session for session name "{self.session_name}".')

        # Azure KeyVault URI
        self.kv_uri = f"https://{self.azure_keyvault}.vault.azure.net"

        try:
            # Initialize Azure SecretClient
            self.azure_client = SecretClient(vault_url=self.kv_uri, credential=credential)
        except Exception as ex:
            raise SecretsStoreException(f'Azure Secrets Store, Not Available. Error: {str(ex)}')

    def get_secret(self, key, default_value=None):
        """
        Retrieve a secret from Azure KeyVault.

        Args:
            key (str): Key of the secret.
            default_value: Default value to return if the secret is not found.

        Returns:
            Secret value if found, else default_value.
        """
        try:
            entry = self.azure_client.get_secret(key)
        except Exception as ex:
            if '(BadParameter) The request URI contains an invalid name' not in str(ex):
                logging.error(str(ex))
            entry = None

        if not entry:
            return default_value

        return entry.value.strip()

    def set_secret(self, key, value):
        """
        Set a secret in Azure KeyVault.

        Args:
            key (str): Key of the secret.
            value: Value of the secret.
        """
        try:
            self.azure_client.set_secret(key, value)
        except Exception as ex:
            logging.error(str(ex))
            raise SecretsStoreException(str(ex))

    def delete_secret(self, key):
        """
        Delete a secret from Azure KeyVault.

        Args:
            key (str): Key of the secret.

        Returns:
            True if the secret is deleted, else False.
        """
        try:
            poller = self.azure_client.begin_delete_secret(key)
            poller.result()
        except Exception as ex:
            logging.error(str(ex))
            raise SecretsStoreException(str(ex))

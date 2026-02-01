import json

from .secret_store import AbstractSecretStore, SecretsStoreException
from shutil import which
from ...misc import run_cmd
import boto3
import logging


class AWSSecretsStore(AbstractSecretStore):
    """
    A class representing an AWS Secrets Store for managing secrets.

    Attributes:
        store_priority (int): Priority of the secret store.
        store_name (str): Name of the secret store.
        application_settings (Settings): An instance of Settings providing application settings.
        aws_profile (str): AWS profile for the secrets store.
        aws_region (str): AWS region for the secrets store.
        aws_session (boto3.session.Session): Boto3 session for interacting with AWS.
        aws_secretsmanager (boto3.client): Boto3 client for AWS Secrets Manager.
    """

    def __init__(self, store_priority, store_name, application_settings, cloud_session_manager) -> None:
        """
        Initialize the AWSSecretsStore.

        Args:
            store_priority (int): Priority of the secret store.
            store_name (str): Name of the secret store.
            application_settings (Settings): An instance of Settings providing application settings.
        """
        super().__init__(store_name, "AWS_Secrets_Store", store_priority, application_settings)

        self.cloud_session_manager = cloud_session_manager

        # Check if AWS CLI is installed
        if not which("aws"):
            raise SecretsStoreException("AWS Secrets Store requires the AWS Command Line Utility to be installed.")

        self.session_name = self.get_store_setting('session_name')
        if not self.session_name:
            raise SecretsStoreException('AWS Secrets Store is missing required session_name parameter.')

        self.aws_session = self.cloud_session_manager.get_session(self.session_name)

        if not self.aws_session:
            raise SecretsStoreException(f'AWS Secrets Store does not have a valid session for session name "{self.session_name}".')

        self.secret_name = self.get_store_setting('secret_name')

        # Initialize AWS Secrets Manager client
        self.aws_secretsmanager = self.aws_session.client('secretsmanager')
        try:
            # Check if AWS Secrets Manager is accessible
            self.aws_secretsmanager.list_secrets()
        except Exception as ex:
            raise SecretsStoreException(f'AWS Secrets Store, Not Available. Error: {str(ex)}')

        logging.info(f'Initialised AWS Secrets Manager {store_name}')

    def get_secret(self, key, default_value=None):
        """
        Get a secret from the AWS Secrets Manager.

        Args:
            key (str): Key of the secret.
            default_value: Default value to return if the secret is not found.

        Returns:
            Secret value if found, else default_value.
        """
        try:
            if self.secret_name is not None:
                entry = self.aws_secretsmanager.get_secret_value(SecretId=self.secret_name)['SecretString']
            else:
                entry = self.aws_secretsmanager.get_secret_value(SecretId=key)['SecretString']
            if entry.startswith('{'):
                entry = json.loads(entry)

            parts = key.split('.')
            if len(parts) == 1:
                return entry
            elif len(parts) == 2:
                return entry[parts[1]]
            else:
                raise SecretsStoreException(f'Unrecognised AWS Key of secret {key}')
        except Exception as ex:
            logging.error(f'{str(ex)} KEY: {key}')
            entry = None

        if not entry:
            entry = default_value

        return entry

    def set_secret(self, key, value):
        """
        Set a secret in the AWS Secrets Manager.

        Args:
            key (str): Key of the secret.
            value: Value of the secret.
        """
        try:
            resp = self.aws_secretsmanager.create_secret(Name=key, SecretString=value, ForceOverwriteReplicaSecret=True)
            if "Name" not in resp:
                raise SecretsStoreException(f'Inconsistent response from AWS: {str(resp)}')
        except Exception as ex:
            logging.error(str(ex))
            raise SecretsStoreException(str(ex))

    def delete_secret(self, key):
        """
        Delete a secret from the AWS Secrets Manager.

        Args:
            key (str): Key of the secret.

        Returns:
            True if the secret is deleted, else False.
        """
        try:
            resp = self.aws_secretsmanager.delete_secret(SecretId=key, ForceDeleteWithoutRecovery=True)
            if "Name" not in resp:
                raise SecretsStoreException(f'Inconsistent response from AWS: {str(resp)}')
        except Exception as ex:
            logging.error(str(ex))
            raise SecretsStoreException(str(ex))

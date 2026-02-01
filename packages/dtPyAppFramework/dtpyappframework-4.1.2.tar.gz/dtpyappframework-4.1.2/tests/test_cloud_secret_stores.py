"""
Comprehensive tests for AWS and Azure cloud secret stores.

This test suite ensures that cloud secret stores correctly handle secret operations,
session management, error handling, and provide proper integration with
AWS Secrets Manager and Azure Key Vault services.
"""

import pytest
import os
import sys
import json
import logging
from unittest.mock import patch, MagicMock, call

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.settings.secrets.secret_store import AbstractSecretStore, SecretsStoreException
from dtPyAppFramework.settings.secrets.aws_secret_store import AWSSecretsStore
from dtPyAppFramework.settings.secrets.azure_secret_store import AzureSecretsStore


class TestAWSSecretsStore:
    """Test AWS Secrets Store implementation."""
    
    def setup_method(self):
        """Setup method run before each test."""
        # Clear any existing logging handlers
        logging.getLogger().handlers = []
    
    @patch('dtPyAppFramework.settings.secrets.aws_secret_store.which', return_value='/usr/bin/aws')
    @patch('logging.info')
    def test_aws_secrets_store_initialization_success(self, mock_log_info, mock_which):
        """Test successful AWS Secrets Store initialization."""
        # Mock dependencies
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        mock_aws_session = MagicMock()
        mock_secrets_client = MagicMock()
        
        # Setup cloud session manager
        mock_cloud_session_manager.get_session.return_value = mock_aws_session
        mock_aws_session.client.return_value = mock_secrets_client
        
        # Setup settings
        mock_store_settings = {'session_name': 'aws_session', 'secret_name': 'app_secrets'}
        
        with patch.object(AbstractSecretStore, 'get_store_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key: mock_store_settings.get(key)
            
            store = AWSSecretsStore(
                store_priority=1,
                store_name="test_aws_store",
                application_settings=mock_app_settings,
                cloud_session_manager=mock_cloud_session_manager
            )
        
        # Verify initialization
        assert store.store_name == "test_aws_store"
        assert store.store_type == "AWS_Secrets_Store"
        assert store.store_priority == 1
        assert store.session_name == "aws_session"
        assert store.secret_name == "app_secrets"
        assert store.aws_session is mock_aws_session
        assert store.aws_secretsmanager is mock_secrets_client
        
        # Verify AWS CLI check
        mock_which.assert_called_once_with("aws")
        
        # Verify session retrieval
        mock_cloud_session_manager.get_session.assert_called_once_with("aws_session")
        
        # Verify Secrets Manager client creation and test
        mock_aws_session.client.assert_called_once_with('secretsmanager')
        mock_secrets_client.list_secrets.assert_called_once()
        
        # Verify logging
        mock_log_info.assert_called_once_with('Initialised AWS Secrets Manager test_aws_store')
    
    @patch('dtPyAppFramework.settings.secrets.aws_secret_store.which', return_value=None)
    def test_aws_secrets_store_no_aws_cli(self, mock_which):
        """Test AWS Secrets Store initialization without AWS CLI."""
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        
        with pytest.raises(SecretsStoreException, match="AWS Secrets Store requires the AWS Command Line Utility"):
            AWSSecretsStore(
                store_priority=1,
                store_name="test_aws_store",
                application_settings=mock_app_settings,
                cloud_session_manager=mock_cloud_session_manager
            )
    
    @patch('dtPyAppFramework.settings.secrets.aws_secret_store.which', return_value='/usr/bin/aws')
    def test_aws_secrets_store_missing_session_name(self, mock_which):
        """Test AWS Secrets Store initialization with missing session_name."""
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        
        with patch.object(AbstractSecretStore, 'get_store_setting', return_value=None):
            with pytest.raises(SecretsStoreException, match="missing required session_name parameter"):
                AWSSecretsStore(
                    store_priority=1,
                    store_name="test_aws_store",
                    application_settings=mock_app_settings,
                    cloud_session_manager=mock_cloud_session_manager
                )
    
    @patch('dtPyAppFramework.settings.secrets.aws_secret_store.which', return_value='/usr/bin/aws')
    def test_aws_secrets_store_invalid_session(self, mock_which):
        """Test AWS Secrets Store initialization with invalid session."""
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        mock_cloud_session_manager.get_session.return_value = None
        
        with patch.object(AbstractSecretStore, 'get_store_setting', return_value='invalid_session'):
            with pytest.raises(SecretsStoreException, match="does not have a valid session"):
                AWSSecretsStore(
                    store_priority=1,
                    store_name="test_aws_store",
                    application_settings=mock_app_settings,
                    cloud_session_manager=mock_cloud_session_manager
                )
    
    @patch('dtPyAppFramework.settings.secrets.aws_secret_store.which', return_value='/usr/bin/aws')
    def test_aws_secrets_store_secrets_manager_unavailable(self, mock_which):
        """Test AWS Secrets Store initialization with unavailable Secrets Manager."""
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        mock_aws_session = MagicMock()
        mock_secrets_client = MagicMock()
        
        # Make list_secrets fail
        mock_secrets_client.list_secrets.side_effect = Exception("Access denied")
        mock_aws_session.client.return_value = mock_secrets_client
        mock_cloud_session_manager.get_session.return_value = mock_aws_session
        
        with patch.object(AbstractSecretStore, 'get_store_setting', return_value='aws_session'):
            with pytest.raises(SecretsStoreException, match="Not Available. Error: Access denied"):
                AWSSecretsStore(
                    store_priority=1,
                    store_name="test_aws_store",
                    application_settings=mock_app_settings,
                    cloud_session_manager=mock_cloud_session_manager
                )
    
    def test_aws_get_secret_with_secret_name(self):
        """Test getting secret when secret_name is configured."""
        # Create a mock store
        store = self._create_mock_aws_store()
        store.secret_name = "app_secrets"
        
        # Mock the AWS response
        mock_response = {'SecretString': '{"db_password": "secret123"}'}
        store.aws_secretsmanager.get_secret_value.return_value = mock_response
        
        result = store.get_secret("app_secrets.db_password")
        
        # Verify the call and result
        store.aws_secretsmanager.get_secret_value.assert_called_once_with(SecretId="app_secrets")
        assert result == "secret123"
    
    def test_aws_get_secret_without_secret_name(self):
        """Test getting secret when secret_name is not configured."""
        store = self._create_mock_aws_store()
        store.secret_name = None
        
        # Mock the AWS response
        mock_response = {'SecretString': 'plain_secret_value'}
        store.aws_secretsmanager.get_secret_value.return_value = mock_response
        
        result = store.get_secret("individual_secret")
        
        # Verify the call and result
        store.aws_secretsmanager.get_secret_value.assert_called_once_with(SecretId="individual_secret")
        assert result == "plain_secret_value"
    
    def test_aws_get_secret_json_parsing(self):
        """Test getting secret with JSON parsing."""
        store = self._create_mock_aws_store()
        store.secret_name = None
        
        # Mock JSON response
        secret_data = {"username": "admin", "password": "secret123", "port": 5432}
        mock_response = {'SecretString': json.dumps(secret_data)}
        store.aws_secretsmanager.get_secret_value.return_value = mock_response
        
        # Test getting the entire JSON object
        result = store.get_secret("json_secret")
        assert result == secret_data
    
    def test_aws_get_secret_dotted_key(self):
        """Test getting secret with dotted key notation."""
        store = self._create_mock_aws_store()
        store.secret_name = None
        
        # Mock JSON response
        secret_data = {"database": {"host": "localhost", "port": 5432}}
        mock_response = {'SecretString': json.dumps(secret_data)}
        store.aws_secretsmanager.get_secret_value.return_value = mock_response
        
        result = store.get_secret("json_secret.database")

        # Verify dotted key access - with secret_name=None, SecretId is the full key
        store.aws_secretsmanager.get_secret_value.assert_called_once_with(SecretId="json_secret.database")
        assert result == {"host": "localhost", "port": 5432}
    
    def test_aws_get_secret_store_name_key(self):
        """Test getting secret using store name as key."""
        store = self._create_mock_aws_store()
        store.secret_name = None
        store.store_name = "my_store"
        
        secret_data = {"key1": "value1", "key2": "value2"}
        mock_response = {'SecretString': json.dumps(secret_data)}
        store.aws_secretsmanager.get_secret_value.return_value = mock_response
        
        result = store.get_secret("my_store")
        
        assert result == secret_data
    
    @patch('logging.error')
    def test_aws_get_secret_exception_handling(self, mock_log_error):
        """Test get_secret exception handling."""
        store = self._create_mock_aws_store()
        store.secret_name = None
        
        # Make get_secret_value raise exception
        store.aws_secretsmanager.get_secret_value.side_effect = Exception("Secret not found")
        
        result = store.get_secret("nonexistent_secret", default_value="default")
        
        # Verify exception handling
        mock_log_error.assert_called_once()
        assert "Secret not found" in mock_log_error.call_args[0][0]
        assert "KEY: nonexistent_secret" in mock_log_error.call_args[0][0]
        assert result == "default"
    
    def test_aws_get_secret_unrecognized_key_format(self):
        """Test get_secret with unrecognized key format (>2 dot-separated parts)."""
        store = self._create_mock_aws_store()
        store.secret_name = "app_secrets"

        mock_response = {'SecretString': '{"key": "value"}'}
        store.aws_secretsmanager.get_secret_value.return_value = mock_response

        # SecretsStoreException is caught by the internal except block and logged,
        # returning default_value (None) instead of propagating
        result = store.get_secret("app_secrets.key1.key2.key3", default_value="fallback")
        assert result == "fallback"
    
    def test_aws_set_secret_success(self):
        """Test successful secret setting."""
        store = self._create_mock_aws_store()
        
        # Mock successful response
        mock_response = {"Name": "test_secret", "ARN": "arn:aws:secretsmanager:..."}
        store.aws_secretsmanager.create_secret.return_value = mock_response
        
        store.set_secret("test_secret", "secret_value")
        
        # Verify the call
        store.aws_secretsmanager.create_secret.assert_called_once_with(
            Name="test_secret",
            SecretString="secret_value",
            ForceOverwriteReplicaSecret=True
        )
    
    def test_aws_set_secret_invalid_response(self):
        """Test set_secret with invalid AWS response."""
        store = self._create_mock_aws_store()
        
        # Mock invalid response (missing Name)
        mock_response = {"ARN": "arn:aws:secretsmanager:..."}
        store.aws_secretsmanager.create_secret.return_value = mock_response
        
        with pytest.raises(SecretsStoreException, match="Inconsistent response from AWS"):
            store.set_secret("test_secret", "secret_value")
    
    @patch('logging.error')
    def test_aws_set_secret_exception(self, mock_log_error):
        """Test set_secret exception handling."""
        store = self._create_mock_aws_store()
        
        # Make create_secret raise exception
        store.aws_secretsmanager.create_secret.side_effect = Exception("Permission denied")
        
        with pytest.raises(SecretsStoreException, match="Permission denied"):
            store.set_secret("test_secret", "secret_value")
        
        mock_log_error.assert_called_once_with("Permission denied")
    
    def test_aws_delete_secret_success(self):
        """Test successful secret deletion."""
        store = self._create_mock_aws_store()
        
        # Mock successful response
        mock_response = {"Name": "test_secret", "ARN": "arn:aws:secretsmanager:..."}
        store.aws_secretsmanager.delete_secret.return_value = mock_response
        
        store.delete_secret("test_secret")
        
        # Verify the call
        store.aws_secretsmanager.delete_secret.assert_called_once_with(
            SecretId="test_secret",
            ForceDeleteWithoutRecovery=True
        )
    
    def test_aws_delete_secret_invalid_response(self):
        """Test delete_secret with invalid AWS response."""
        store = self._create_mock_aws_store()
        
        # Mock invalid response
        mock_response = {"ARN": "arn:aws:secretsmanager:..."}
        store.aws_secretsmanager.delete_secret.return_value = mock_response
        
        with pytest.raises(SecretsStoreException, match="Inconsistent response from AWS"):
            store.delete_secret("test_secret")
    
    @patch('logging.error')
    def test_aws_delete_secret_exception(self, mock_log_error):
        """Test delete_secret exception handling."""
        store = self._create_mock_aws_store()
        
        # Make delete_secret raise exception
        store.aws_secretsmanager.delete_secret.side_effect = Exception("Secret not found")
        
        with pytest.raises(SecretsStoreException, match="Secret not found"):
            store.delete_secret("test_secret")
        
        mock_log_error.assert_called_once_with("Secret not found")
    
    def _create_mock_aws_store(self):
        """Helper method to create a mock AWS Secrets Store."""
        store = AWSSecretsStore.__new__(AWSSecretsStore)
        store.store_name = "test_store"
        store.store_type = "AWS_Secrets_Store"
        store.store_priority = 1
        store.session_name = "test_session"
        store.secret_name = None
        store.aws_session = MagicMock()
        store.aws_secretsmanager = MagicMock()
        return store


class TestAzureSecretsStore:
    """Test Azure Secrets Store implementation."""
    
    def setup_method(self):
        """Setup method run before each test."""
        logging.getLogger().handlers = []
    
    def test_azure_secrets_store_initialization_success(self):
        """Test successful Azure Secrets Store initialization."""
        # Mock dependencies
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        mock_azure_credential = MagicMock()
        mock_secret_client = MagicMock()
        
        # Setup cloud session manager
        mock_cloud_session_manager.get_session.return_value = mock_azure_credential
        
        # Setup settings
        mock_store_settings = {
            'azure_keyvault': 'mykeyvault',
            'session_name': 'azure_session'
        }
        
        with patch.object(AbstractSecretStore, 'get_store_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key: mock_store_settings.get(key)
            
            with patch('dtPyAppFramework.settings.secrets.azure_secret_store.SecretClient') as mock_client_class:
                mock_client_class.return_value = mock_secret_client
                
                store = AzureSecretsStore(
                    store_priority=1,
                    store_name="test_azure_store",
                    application_settings=mock_app_settings,
                    cloud_session_manager=mock_cloud_session_manager
                )
        
        # Verify initialization
        assert store.store_name == "test_azure_store"
        assert store.store_type == "Azure_Secrets_Store"
        assert store.store_priority == 1
        assert store.session_name == "azure_session"
        assert store.azure_keyvault == "mykeyvault"
        assert store.kv_uri == "https://mykeyvault.vault.azure.net"
        assert store.azure_client is mock_secret_client
        
        # Verify session retrieval
        mock_cloud_session_manager.get_session.assert_called_once_with("azure_session")
        
        # Verify SecretClient creation
        mock_client_class.assert_called_once_with(
            vault_url="https://mykeyvault.vault.azure.net",
            credential=mock_azure_credential
        )
    
    def test_azure_secrets_store_missing_keyvault(self):
        """Test Azure Secrets Store initialization with missing azure_keyvault."""
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        
        mock_store_settings = {'session_name': 'azure_session'}
        
        with patch.object(AbstractSecretStore, 'get_store_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key: mock_store_settings.get(key)
            
            with pytest.raises(SecretsStoreException, match="missing required azure_keyvault parameter"):
                AzureSecretsStore(
                    store_priority=1,
                    store_name="test_azure_store",
                    application_settings=mock_app_settings,
                    cloud_session_manager=mock_cloud_session_manager
                )
    
    def test_azure_secrets_store_missing_session_name(self):
        """Test Azure Secrets Store initialization with missing session_name."""
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        
        mock_store_settings = {'azure_keyvault': 'mykeyvault'}
        
        with patch.object(AbstractSecretStore, 'get_store_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key: mock_store_settings.get(key)
            
            with pytest.raises(SecretsStoreException, match="missing required session_name parameter"):
                AzureSecretsStore(
                    store_priority=1,
                    store_name="test_azure_store",
                    application_settings=mock_app_settings,
                    cloud_session_manager=mock_cloud_session_manager
                )
    
    def test_azure_secrets_store_invalid_session(self):
        """Test Azure Secrets Store initialization with invalid session."""
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        mock_cloud_session_manager.get_session.return_value = None
        
        mock_store_settings = {
            'azure_keyvault': 'mykeyvault',
            'session_name': 'invalid_session'
        }
        
        with patch.object(AbstractSecretStore, 'get_store_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key: mock_store_settings.get(key)
            
            with pytest.raises(SecretsStoreException, match="does not have a valid session"):
                AzureSecretsStore(
                    store_priority=1,
                    store_name="test_azure_store",
                    application_settings=mock_app_settings,
                    cloud_session_manager=mock_cloud_session_manager
                )
    
    def test_azure_secrets_store_client_initialization_failure(self):
        """Test Azure Secrets Store initialization with SecretClient failure."""
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        mock_azure_credential = MagicMock()
        mock_cloud_session_manager.get_session.return_value = mock_azure_credential
        
        mock_store_settings = {
            'azure_keyvault': 'mykeyvault',
            'session_name': 'azure_session'
        }
        
        with patch.object(AbstractSecretStore, 'get_store_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key: mock_store_settings.get(key)
            
            with patch('dtPyAppFramework.settings.secrets.azure_secret_store.SecretClient') as mock_client_class:
                mock_client_class.side_effect = Exception("Authentication failed")
                
                with pytest.raises(SecretsStoreException, match="Not Available. Error: Authentication failed"):
                    AzureSecretsStore(
                        store_priority=1,
                        store_name="test_azure_store",
                        application_settings=mock_app_settings,
                        cloud_session_manager=mock_cloud_session_manager
                    )
    
    def test_azure_get_secret_success(self):
        """Test successful secret retrieval from Azure Key Vault."""
        store = self._create_mock_azure_store()
        
        # Mock Azure response
        mock_secret = MagicMock()
        mock_secret.value = "  secret_value_123  "  # With whitespace to test stripping
        store.azure_client.get_secret.return_value = mock_secret
        
        result = store.get_secret("test_secret")
        
        # Verify the call and result
        store.azure_client.get_secret.assert_called_once_with("test_secret")
        assert result == "secret_value_123"  # Should be stripped
    
    def test_azure_get_secret_with_default(self):
        """Test getting secret with default value when secret not found."""
        store = self._create_mock_azure_store()
        
        # Make get_secret raise exception
        store.azure_client.get_secret.side_effect = Exception("Secret not found")
        
        result = store.get_secret("nonexistent_secret", default_value="default_value")
        
        assert result == "default_value"
    
    @patch('logging.error')
    def test_azure_get_secret_bad_parameter_exception(self, mock_log_error):
        """Test get_secret with BadParameter exception (should not log)."""
        store = self._create_mock_azure_store()
        
        # BadParameter exceptions should not be logged
        store.azure_client.get_secret.side_effect = Exception("(BadParameter) The request URI contains an invalid name")
        
        result = store.get_secret("invalid-name", default_value="default")
        
        # Verify no error logging for BadParameter
        mock_log_error.assert_not_called()
        assert result == "default"
    
    @patch('logging.error')
    def test_azure_get_secret_other_exception(self, mock_log_error):
        """Test get_secret with other exceptions (should log)."""
        store = self._create_mock_azure_store()
        
        # Other exceptions should be logged
        store.azure_client.get_secret.side_effect = Exception("Permission denied")
        
        result = store.get_secret("test_secret", default_value="default")
        
        # Verify error logging for other exceptions
        mock_log_error.assert_called_once_with("Permission denied")
        assert result == "default"
    
    def test_azure_set_secret_success(self):
        """Test successful secret setting in Azure Key Vault."""
        store = self._create_mock_azure_store()
        
        store.set_secret("test_secret", "secret_value")
        
        # Verify the call
        store.azure_client.set_secret.assert_called_once_with("test_secret", "secret_value")
    
    @patch('logging.error')
    def test_azure_set_secret_exception(self, mock_log_error):
        """Test set_secret exception handling."""
        store = self._create_mock_azure_store()
        
        # Make set_secret raise exception
        store.azure_client.set_secret.side_effect = Exception("Permission denied")
        
        with pytest.raises(SecretsStoreException, match="Permission denied"):
            store.set_secret("test_secret", "secret_value")
        
        mock_log_error.assert_called_once_with("Permission denied")
    
    def test_azure_delete_secret_success(self):
        """Test successful secret deletion from Azure Key Vault."""
        store = self._create_mock_azure_store()
        
        # Mock the delete operation
        mock_poller = MagicMock()
        mock_deleted_secret = MagicMock()
        mock_poller.result.return_value = mock_deleted_secret
        store.azure_client.begin_delete_secret.return_value = mock_poller
        
        store.delete_secret("test_secret")
        
        # Verify the call
        store.azure_client.begin_delete_secret.assert_called_once_with("test_secret")
        mock_poller.result.assert_called_once()
    
    @patch('logging.error')
    def test_azure_delete_secret_exception(self, mock_log_error):
        """Test delete_secret exception handling."""
        store = self._create_mock_azure_store()
        
        # Make begin_delete_secret raise exception
        store.azure_client.begin_delete_secret.side_effect = Exception("Secret not found")
        
        with pytest.raises(SecretsStoreException, match="Secret not found"):
            store.delete_secret("test_secret")
        
        mock_log_error.assert_called_once_with("Secret not found")
    
    def _create_mock_azure_store(self):
        """Helper method to create a mock Azure Secrets Store."""
        store = AzureSecretsStore.__new__(AzureSecretsStore)
        store.store_name = "test_store"
        store.store_type = "Azure_Secrets_Store"
        store.store_priority = 1
        store.session_name = "test_session"
        store.azure_keyvault = "mykeyvault"
        store.kv_uri = "https://mykeyvault.vault.azure.net"
        store.azure_client = MagicMock()
        return store


class TestSecretStoreInheritance:
    """Test inheritance and polymorphism of secret stores."""
    
    def test_secret_stores_inherit_from_abstract(self):
        """Test that secret stores properly inherit from AbstractSecretStore."""
        # Both should inherit from AbstractSecretStore
        assert issubclass(AWSSecretsStore, AbstractSecretStore)
        assert issubclass(AzureSecretsStore, AbstractSecretStore)
    
    def test_polymorphic_behavior(self):
        """Test polymorphic behavior of secret stores."""
        def process_secret_store(store: AbstractSecretStore):
            """Function that accepts any AbstractSecretStore."""
            return {
                'name': store.store_name,
                'type': store.store_type,
                'priority': store.store_priority
            }
        
        # Create mock stores
        aws_store = AWSSecretsStore.__new__(AWSSecretsStore)
        aws_store.store_name = "aws_store"
        aws_store.store_type = "AWS_Secrets_Store"
        aws_store.store_priority = 1
        
        azure_store = AzureSecretsStore.__new__(AzureSecretsStore)
        azure_store.store_name = "azure_store"
        azure_store.store_type = "Azure_Secrets_Store"
        azure_store.store_priority = 2
        
        # Both should work polymorphically
        aws_result = process_secret_store(aws_store)
        azure_result = process_secret_store(azure_store)
        
        assert aws_result['name'] == 'aws_store'
        assert aws_result['type'] == 'AWS_Secrets_Store'
        assert aws_result['priority'] == 1
        
        assert azure_result['name'] == 'azure_store'
        assert azure_result['type'] == 'Azure_Secrets_Store'
        assert azure_result['priority'] == 2


class TestSecretStoreIntegration:
    """Test integration scenarios for secret stores."""
    
    @patch('dtPyAppFramework.settings.secrets.aws_secret_store.which', return_value='/usr/bin/aws')
    @patch('logging.info')
    def test_aws_store_integration_scenario(self, mock_log_info, mock_which):
        """Test AWS store in a realistic integration scenario."""
        # Mock all dependencies
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        mock_aws_session = MagicMock()
        mock_secrets_client = MagicMock()
        
        # Setup the full chain
        mock_cloud_session_manager.get_session.return_value = mock_aws_session
        mock_aws_session.client.return_value = mock_secrets_client
        mock_secrets_client.list_secrets.return_value = {"SecretList": []}
        
        # Setup settings
        mock_store_settings = {
            'session_name': 'prod_aws_session',
            'secret_name': 'myapp_secrets'
        }
        
        with patch.object(AbstractSecretStore, 'get_store_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key: mock_store_settings.get(key)
            
            # Create store
            store = AWSSecretsStore(
                store_priority=1,
                store_name="production_secrets",
                application_settings=mock_app_settings,
                cloud_session_manager=mock_cloud_session_manager
            )
            
            # Test secret operations
            # 1. Get a secret (JSON format)
            secret_data = {"db_password": "prod_password", "api_key": "key123"}
            mock_secrets_client.get_secret_value.return_value = {
                'SecretString': json.dumps(secret_data)
            }
            
            db_password = store.get_secret("myapp_secrets.db_password")
            assert db_password == "prod_password"
            
            # 2. Set a new secret
            mock_secrets_client.create_secret.return_value = {"Name": "new_secret"}
            store.set_secret("new_secret", "new_value")
            
            # 3. Delete a secret
            mock_secrets_client.delete_secret.return_value = {"Name": "old_secret"}
            store.delete_secret("old_secret")
        
        # Verify initialization logging
        mock_log_info.assert_called_once_with('Initialised AWS Secrets Manager production_secrets')
    
    def test_azure_store_integration_scenario(self):
        """Test Azure store in a realistic integration scenario."""
        # Mock all dependencies
        mock_app_settings = MagicMock()
        mock_cloud_session_manager = MagicMock()
        mock_azure_credential = MagicMock()
        mock_secret_client = MagicMock()
        
        # Setup the full chain
        mock_cloud_session_manager.get_session.return_value = mock_azure_credential
        
        # Setup settings
        mock_store_settings = {
            'azure_keyvault': 'production-kv',
            'session_name': 'prod_azure_session'
        }
        
        with patch.object(AbstractSecretStore, 'get_store_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key: mock_store_settings.get(key)
            
            with patch('dtPyAppFramework.settings.secrets.azure_secret_store.SecretClient') as mock_client_class:
                mock_client_class.return_value = mock_secret_client
                
                # Create store
                store = AzureSecretsStore(
                    store_priority=1,
                    store_name="production_azure_secrets",
                    application_settings=mock_app_settings,
                    cloud_session_manager=mock_cloud_session_manager
                )
                
                # Test secret operations
                # 1. Get a secret
                mock_secret = MagicMock()
                mock_secret.value = "production_database_password"
                mock_secret_client.get_secret.return_value = mock_secret
                
                password = store.get_secret("database-password")
                assert password == "production_database_password"
                
                # 2. Set a new secret
                store.set_secret("api-key", "new_api_key_value")
                mock_secret_client.set_secret.assert_called_with("api-key", "new_api_key_value")
                
                # 3. Delete a secret
                mock_poller = MagicMock()
                mock_secret_client.begin_delete_secret.return_value = mock_poller
                store.delete_secret("old-secret")
                mock_secret_client.begin_delete_secret.assert_called_with("old-secret")
                mock_poller.result.assert_called_once()
        
        # Verify client was created with correct parameters
        mock_client_class.assert_called_once_with(
            vault_url="https://production-kv.vault.azure.net",
            credential=mock_azure_credential
        )


class TestSecretStoreErrorScenarios:
    """Test various error scenarios and edge cases."""
    
    @patch('dtPyAppFramework.settings.secrets.aws_secret_store.which', return_value='/usr/bin/aws')
    def test_aws_store_with_corrupted_json(self, mock_which):
        """Test AWS store handling of corrupted JSON in secrets."""
        store = self._create_mock_aws_store()
        store.secret_name = None
        
        # Mock response with invalid JSON
        mock_response = {'SecretString': '{"invalid": json"}'}  # Invalid JSON
        store.aws_secretsmanager.get_secret_value.return_value = mock_response
        
        with patch('logging.error') as mock_log_error:
            result = store.get_secret("corrupted_json", default_value="default")
            
            # Should handle JSON parsing error gracefully
            assert result == "default"
            mock_log_error.assert_called_once()
    
    def test_azure_store_with_empty_secret_value(self):
        """Test Azure store handling of empty secret values."""
        store = self._create_mock_azure_store()
        
        # Mock Azure response with empty value
        mock_secret = MagicMock()
        mock_secret.value = "   "  # Only whitespace
        store.azure_client.get_secret.return_value = mock_secret
        
        result = store.get_secret("empty_secret")
        
        # Should return empty string after stripping
        assert result == ""
    
    def test_aws_store_network_timeout_scenario(self):
        """Test AWS store handling network timeouts."""
        store = self._create_mock_aws_store()
        
        # Simulate network timeout
        import socket
        store.aws_secretsmanager.get_secret_value.side_effect = socket.timeout("Network timeout")
        
        with patch('logging.error') as mock_log_error:
            result = store.get_secret("test_secret", default_value="fallback")
            
            assert result == "fallback"
            mock_log_error.assert_called_once()
    
    def test_azure_store_authentication_failure(self):
        """Test Azure store handling authentication failures."""
        store = self._create_mock_azure_store()
        
        # Simulate authentication failure
        from azure.core.exceptions import ClientAuthenticationError
        store.azure_client.get_secret.side_effect = ClientAuthenticationError("Authentication failed")
        
        with patch('logging.error') as mock_log_error:
            result = store.get_secret("test_secret", default_value="fallback")
            
            assert result == "fallback"
            mock_log_error.assert_called_once_with("Authentication failed")
    
    def _create_mock_aws_store(self):
        """Helper method to create a mock AWS Secrets Store."""
        store = AWSSecretsStore.__new__(AWSSecretsStore)
        store.store_name = "test_store"
        store.store_type = "AWS_Secrets_Store"
        store.store_priority = 1
        store.session_name = "test_session"
        store.secret_name = None
        store.aws_session = MagicMock()
        store.aws_secretsmanager = MagicMock()
        return store
    
    def _create_mock_azure_store(self):
        """Helper method to create a mock Azure Secrets Store."""
        store = AzureSecretsStore.__new__(AzureSecretsStore)
        store.store_name = "test_store"
        store.store_type = "Azure_Secrets_Store"
        store.store_priority = 1
        store.session_name = "test_session"
        store.azure_keyvault = "mykeyvault"
        store.kv_uri = "https://mykeyvault.vault.azure.net"
        store.azure_client = MagicMock()
        return store


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
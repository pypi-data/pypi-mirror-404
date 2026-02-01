"""
Comprehensive tests for AWS and Azure cloud session management.

This test suite ensures that cloud session classes correctly handle authentication,
session initialization, error handling, and provide proper integration with
AWS and Azure services.
"""

import pytest
import os
import sys
import logging
from unittest.mock import patch, MagicMock, call

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dtPyAppFramework.cloud.cloud_session import AbstractCloudSession
from dtPyAppFramework.cloud.aws import AWSCloudSession
from dtPyAppFramework.cloud.azure import AzureCloudSession


class TestAbstractCloudSession:
    """Test AbstractCloudSession base class functionality."""

    def test_abstract_cloud_session_initialization(self):
        """Test AbstractCloudSession basic initialization."""
        settings = {
            'setting1': 'value1',
            'setting2': 'value2'
        }

        session = AbstractCloudSession(
            name="test_session",
            session_type="test_type",
            settings=settings
        )

        assert session.name == "test_session"
        assert session.session_type == "test_type"
        assert session.settings == settings
        assert session.session_available is False

    def test_get_setting_existing_key(self):
        """Test get_setting with existing key."""
        settings = {
            'key1': 'value1',
            'key2': 42,
            'key3': True
        }

        session = AbstractCloudSession("test", "test", settings)

        assert session.get_setting('key1') == 'value1'
        assert session.get_setting('key2') == 42
        assert session.get_setting('key3') is True

    def test_get_setting_missing_key(self):
        """Test get_setting with missing key returns None."""
        settings = {'existing_key': 'value'}

        session = AbstractCloudSession("test", "test", settings)

        assert session.get_setting('missing_key') is None
        assert session.get_setting('') is None

    def test_get_setting_empty_settings(self):
        """Test get_setting with empty settings."""
        session = AbstractCloudSession("test", "test", {})

        assert session.get_setting('any_key') is None

    def test_abstract_get_session_method(self):
        """Test that get_session is abstract and must be implemented."""
        session = AbstractCloudSession("test", "test", {})

        with pytest.raises(NotImplementedError):
            session.get_session()


class TestAWSCloudSession:
    """Test AWS cloud session implementation."""

    def setup_method(self):
        """Setup method run before each test."""
        logging.getLogger().handlers = []

    def test_aws_session_missing_profile(self):
        """Test AWS session creation with missing aws_profile."""
        settings = {
            'aws_region': 'us-east-1'
            # Missing aws_profile
        }

        with patch('dtPyAppFramework.cloud.aws.logging') as _:
            session = AWSCloudSession(
                name="test_aws",
                session_type="aws",
                settings=settings
            )

        assert session.session_available is False
        # aws_session attribute should not exist when init returns early
        assert not hasattr(session, 'aws_session')

    def test_aws_session_missing_region(self):
        """Test AWS session creation with missing aws_region."""
        settings = {
            'aws_profile': 'key'
            # Missing aws_region
        }

        with patch('dtPyAppFramework.cloud.aws.logging') as _:
            session = AWSCloudSession(
                name="test_aws",
                session_type="aws",
                settings=settings
            )

        assert session.session_available is False
        assert not hasattr(session, 'aws_session')

    @patch('boto3.session.Session')
    def test_aws_session_key_profile_success(self, mock_boto_session):
        """Test successful AWS session creation with key profile."""
        mock_session_instance = MagicMock()
        mock_boto_session.return_value = mock_session_instance

        settings = {
            'aws_profile': 'key',
            'aws_region': 'us-west-2',
            'aws_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
            'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        }

        session = AWSCloudSession(
            name="test_aws",
            session_type="aws",
            settings=settings
        )

        # Verify session creation
        mock_boto_session.assert_called_once_with(
            region_name='us-west-2',
            aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
            aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        )

        assert session.session_available is True
        assert session.aws_session is mock_session_instance

    def test_aws_session_key_profile_missing_credentials(self):
        """Test AWS session creation with key profile but missing credentials."""
        settings = {
            'aws_profile': 'key',
            'aws_region': 'us-west-2'
            # Missing aws_access_key_id and aws_secret_access_key
        }

        with patch('dtPyAppFramework.cloud.aws.logging') as _:
            session = AWSCloudSession(
                name="test_aws",
                session_type="aws",
                settings=settings
            )

        assert session.session_available is False
        assert session.aws_session is None

    @patch('boto3.session.Session')
    def test_aws_session_ec2_profile(self, mock_boto_session):
        """Test AWS session creation with EC2 instance profile."""
        mock_session_instance = MagicMock()
        mock_boto_session.return_value = mock_session_instance

        settings = {
            'aws_profile': 'ec2',
            'aws_region': 'eu-central-1'
        }

        session = AWSCloudSession(
            name="test_aws_ec2",
            session_type="aws",
            settings=settings
        )

        # Verify session creation with region only
        mock_boto_session.assert_called_once_with(region_name='eu-central-1')
        assert session.session_available is True
        assert session.aws_session is mock_session_instance

    @patch('dtPyAppFramework.cloud.aws.run_cmd')
    @patch('boto3.session.Session')
    def test_aws_session_sso_profile_success(self, mock_boto_session, mock_run_cmd):
        """Test successful AWS session creation with SSO profile."""
        mock_session_instance = MagicMock()
        mock_boto_session.return_value = mock_session_instance
        mock_run_cmd.return_value = "Successfully logged into Start URL: https://example.com"

        settings = {
            'aws_profile': 'sso:my-sso-profile',
            'aws_region': 'ap-southeast-2'
        }

        session = AWSCloudSession(
            name="test_aws_sso",
            session_type="aws",
            settings=settings
        )

        # Verify SSO login command was called
        mock_run_cmd.assert_called_once_with('aws sso login --profile my-sso-profile')

        # Verify session creation
        mock_boto_session.assert_called_once_with(region_name='ap-southeast-2')
        assert session.session_available is True
        assert session.aws_session is mock_session_instance

    @patch('dtPyAppFramework.cloud.aws.run_cmd')
    def test_aws_session_sso_profile_login_failure(self, mock_run_cmd):
        """Test AWS session creation with SSO login failure."""
        mock_run_cmd.return_value = "Error: Failed to login"

        settings = {
            'aws_profile': 'sso:failed-profile',
            'aws_region': 'us-east-1'
        }

        with patch('dtPyAppFramework.cloud.aws.logging') as _:
            session = AWSCloudSession(
                name="test_aws_sso_fail",
                session_type="aws",
                settings=settings
            )

        # Verify SSO login was attempted
        mock_run_cmd.assert_called_once_with('aws sso login --profile failed-profile')
        assert session.session_available is False
        assert session.aws_session is None

    @patch('dtPyAppFramework.cloud.aws.run_cmd')
    def test_aws_session_sso_profile_no_response(self, mock_run_cmd):
        """Test AWS session creation with SSO command returning None."""
        mock_run_cmd.return_value = None

        settings = {
            'aws_profile': 'sso:no-response-profile',
            'aws_region': 'us-west-1'
        }

        with patch('dtPyAppFramework.cloud.aws.logging') as _:
            session = AWSCloudSession(
                name="test_aws_sso_none",
                session_type="aws",
                settings=settings
            )

        assert session.session_available is False

    def test_aws_session_unrecognized_profile_type(self):
        """Test AWS session creation with unrecognized profile type."""
        settings = {
            'aws_profile': 'unknown_profile_type',
            'aws_region': 'us-east-1'
        }

        with patch('dtPyAppFramework.cloud.aws.logging') as _:
            session = AWSCloudSession(
                name="test_aws_unknown",
                session_type="aws",
                settings=settings
            )

        assert session.session_available is False
        assert session.aws_session is None

    def test_aws_session_get_session(self):
        """Test get_session returns the AWS session."""
        settings = {
            'aws_profile': 'ec2',
            'aws_region': 'us-east-1'
        }

        with patch('boto3.session.Session') as mock_boto_session:
            mock_session_instance = MagicMock()
            mock_boto_session.return_value = mock_session_instance

            session = AWSCloudSession(
                name="test_aws",
                session_type="aws",
                settings=settings
            )

            result = session.get_session()
            assert result is mock_session_instance


class TestAzureCloudSession:
    """Test Azure cloud session implementation."""

    def setup_method(self):
        """Setup method run before each test."""
        logging.getLogger().handlers = []

    def test_azure_session_missing_identity_type(self):
        """Test Azure session creation with missing azure_identity_type."""
        settings = {
            'azure_tenant_id': 'tenant-123'
            # Missing azure_identity_type
        }

        with patch('dtPyAppFramework.cloud.azure.logging') as _:
            session = AzureCloudSession(
                name="test_azure",
                session_type="azure",
                settings=settings
            )

        assert session.session_available is False
        # azure_session attribute should not exist when init returns early
        assert not hasattr(session, 'azure_session')

    def test_azure_session_missing_tenant_id(self):
        """Test Azure session creation with missing azure_tenant_id."""
        settings = {
            'azure_identity_type': 'certificate'
            # Missing azure_tenant_id
        }

        with patch('dtPyAppFramework.cloud.azure.logging') as _:
            session = AzureCloudSession(
                name="test_azure",
                session_type="azure",
                settings=settings
            )

        assert session.session_available is False

    @patch('dtPyAppFramework.cloud.azure.CertificateCredential')
    def test_azure_session_certificate_identity_success(self, mock_cert_credential):
        """Test successful Azure session creation with certificate identity."""
        mock_credential_instance = MagicMock()
        mock_cert_credential.return_value = mock_credential_instance

        settings = {
            'azure_identity_type': 'certificate',
            'azure_tenant_id': 'tenant-456',
            'azure_client_id': 'client-789',
            'certificate_path': '/path/to/cert.p12',
            'certificate_password': 'cert_password'
        }

        session = AzureCloudSession(
            name="test_azure_cert",
            session_type="azure",
            settings=settings
        )

        # Verify credential creation
        mock_cert_credential.assert_called_once_with(
            tenant_id='tenant-456',
            client_id='client-789',
            certificate_path='/path/to/cert.p12',
            password='cert_password'
        )

        assert session.session_available is True
        assert session.azure_session is mock_credential_instance

    @patch('dtPyAppFramework.cloud.azure.CertificateCredential')
    def test_azure_session_certificate_identity_without_password(self, mock_cert_credential):
        """Test Azure session creation with certificate identity without password."""
        mock_credential_instance = MagicMock()
        mock_cert_credential.return_value = mock_credential_instance

        settings = {
            'azure_identity_type': 'certificate',
            'azure_tenant_id': 'tenant-456',
            'azure_client_id': 'client-789',
            'certificate_path': '/path/to/cert.p12'
            # No certificate_password
        }

        session = AzureCloudSession(
            name="test_azure_cert_no_pwd",
            session_type="azure",
            settings=settings
        )

        # Verify credential creation with None password
        mock_cert_credential.assert_called_once_with(
            tenant_id='tenant-456',
            client_id='client-789',
            certificate_path='/path/to/cert.p12',
            password=None
        )

        assert session.session_available is True

    def test_azure_session_certificate_identity_missing_params(self):
        """Test Azure session creation with certificate identity missing parameters."""
        settings = {
            'azure_identity_type': 'certificate',
            'azure_tenant_id': 'tenant-456'
            # Missing azure_client_id and certificate_path
        }

        with patch('dtPyAppFramework.cloud.azure.logging') as _:
            session = AzureCloudSession(
                name="test_azure_cert_missing",
                session_type="azure",
                settings=settings
            )

        assert session.session_available is False
        assert session.azure_session is None

    @patch('dtPyAppFramework.cloud.azure.ClientSecretCredential')
    def test_azure_session_key_identity_success(self, mock_client_secret):
        """Test successful Azure session creation with client secret identity."""
        mock_credential_instance = MagicMock()
        mock_client_secret.return_value = mock_credential_instance

        settings = {
            'azure_identity_type': 'key',
            'azure_tenant_id': 'tenant-123',
            'azure_client_id': 'client-456',
            'client_secret': 'super_secret_value'
        }

        session = AzureCloudSession(
            name="test_azure_secret",
            session_type="azure",
            settings=settings
        )

        # Verify credential creation
        mock_client_secret.assert_called_once_with(
            tenant_id='tenant-123',
            client_id='client-456',
            client_secret='super_secret_value'
        )

        assert session.session_available is True
        assert session.azure_session is mock_credential_instance

    def test_azure_session_key_identity_missing_params(self):
        """Test Azure session creation with key identity missing parameters."""
        settings = {
            'azure_identity_type': 'key',
            'azure_tenant_id': 'tenant-123',
            'azure_client_id': 'client-456'
            # Missing client_secret
        }

        with patch('dtPyAppFramework.cloud.azure.logging') as _:
            session = AzureCloudSession(
                name="test_azure_secret_missing",
                session_type="azure",
                settings=settings
            )

        assert session.session_available is False

    @patch('dtPyAppFramework.cloud.azure.InteractiveBrowserCredential')
    def test_azure_session_interactive_browser_identity(self, mock_interactive_browser):
        """Test Azure session creation with interactive browser identity."""
        mock_credential_instance = MagicMock()
        mock_interactive_browser.return_value = mock_credential_instance

        settings = {
            'azure_identity_type': 'interactive_browser',
            'azure_tenant_id': 'tenant-789'
        }

        session = AzureCloudSession(
            name="test_azure_browser",
            session_type="azure",
            settings=settings
        )

        # Verify credential creation
        mock_interactive_browser.assert_called_once_with(tenant_id='tenant-789')

        assert session.session_available is True
        assert session.azure_session is mock_credential_instance

    def test_azure_session_unrecognized_identity_type(self):
        """Test Azure session creation with unrecognized identity type."""
        settings = {
            'azure_identity_type': 'unknown_type',
            'azure_tenant_id': 'tenant-123'
        }

        with patch('dtPyAppFramework.cloud.azure.logging') as _:
            session = AzureCloudSession(
                name="test_azure_unknown",
                session_type="azure",
                settings=settings
            )

        assert session.session_available is False
        assert session.azure_session is None

    def test_azure_session_get_session(self):
        """Test get_session returns the Azure session."""
        settings = {
            'azure_identity_type': 'interactive_browser',
            'azure_tenant_id': 'tenant-123'
        }

        with patch('dtPyAppFramework.cloud.azure.InteractiveBrowserCredential') as mock_interactive:
            mock_credential_instance = MagicMock()
            mock_interactive.return_value = mock_credential_instance

            session = AzureCloudSession(
                name="test_azure",
                session_type="azure",
                settings=settings
            )

            result = session.get_session()
            assert result is mock_credential_instance


class TestCloudSessionInheritance:
    """Test inheritance and polymorphism of cloud sessions."""

    def test_cloud_sessions_inherit_from_abstract(self):
        """Test that cloud sessions properly inherit from AbstractCloudSession."""
        # Both should inherit from AbstractCloudSession
        assert issubclass(AWSCloudSession, AbstractCloudSession)
        assert issubclass(AzureCloudSession, AbstractCloudSession)

        # Test instantiation
        with patch('boto3.session.Session'):
            aws_session = AWSCloudSession("aws_test", "aws", {
                'aws_profile': 'ec2',
                'aws_region': 'us-east-1'
            })

        with patch('dtPyAppFramework.cloud.azure.InteractiveBrowserCredential'):
            azure_session = AzureCloudSession("azure_test", "azure", {
                'azure_identity_type': 'interactive_browser',
                'azure_tenant_id': 'tenant-123'
            })

        # Both should have AbstractCloudSession methods
        assert hasattr(aws_session, 'get_setting')
        assert hasattr(azure_session, 'get_setting')
        assert hasattr(aws_session, 'get_session')
        assert hasattr(azure_session, 'get_session')

    def test_polymorphic_behavior(self):
        """Test polymorphic behavior of cloud sessions."""
        def process_cloud_session(session: AbstractCloudSession):
            """Function that accepts any AbstractCloudSession."""
            return {
                'name': session.name,
                'type': session.session_type,
                'available': session.session_available,
                'session': session.get_session()
            }

        with patch('boto3.session.Session') as mock_boto:
            mock_aws_session = MagicMock()
            mock_boto.return_value = mock_aws_session

            aws_session = AWSCloudSession("aws_poly", "aws", {
                'aws_profile': 'ec2',
                'aws_region': 'us-east-1'
            })

        with patch('dtPyAppFramework.cloud.azure.InteractiveBrowserCredential') as mock_azure:
            mock_azure_session = MagicMock()
            mock_azure.return_value = mock_azure_session

            azure_session = AzureCloudSession("azure_poly", "azure", {
                'azure_identity_type': 'interactive_browser',
                'azure_tenant_id': 'tenant-123'
            })

        # Both should work polymorphically
        aws_result = process_cloud_session(aws_session)
        azure_result = process_cloud_session(azure_session)

        assert aws_result['name'] == 'aws_poly'
        assert aws_result['type'] == 'aws'
        assert aws_result['available'] is True
        assert aws_result['session'] is mock_aws_session

        assert azure_result['name'] == 'azure_poly'
        assert azure_result['type'] == 'azure'
        assert azure_result['available'] is True
        assert azure_result['session'] is mock_azure_session


class TestCloudSessionErrorScenarios:
    """Test various error scenarios and edge cases."""

    def test_empty_settings(self):
        """Test cloud sessions with empty settings."""
        with patch('dtPyAppFramework.cloud.aws.logging'):
            aws_session = AWSCloudSession("empty_aws", "aws", {})
        with patch('dtPyAppFramework.cloud.azure.logging'):
            azure_session = AzureCloudSession("empty_azure", "azure", {})

        # Both should fail gracefully
        assert aws_session.session_available is False
        assert azure_session.session_available is False

    def test_none_settings(self):
        """Test cloud sessions with None settings."""
        with pytest.raises(AttributeError):
            # This should raise AttributeError when trying to get from None
            AWSCloudSession("none_aws", "aws", None)

    def test_aws_session_initialization_exception(self):
        """Test AWS session when boto3 initialization fails."""
        settings = {
            'aws_profile': 'ec2',
            'aws_region': 'us-east-1'
        }

        with patch('boto3.session.Session', side_effect=Exception("Boto3 failed")):
            with pytest.raises(Exception, match="Boto3 failed"):
                AWSCloudSession("aws_exception", "aws", settings)

    def test_azure_session_initialization_exception(self):
        """Test Azure session when Azure credential initialization fails."""
        settings = {
            'azure_identity_type': 'interactive_browser',
            'azure_tenant_id': 'tenant-123'
        }

        with patch('dtPyAppFramework.cloud.azure.InteractiveBrowserCredential', side_effect=Exception("Azure failed")):
            with pytest.raises(Exception, match="Azure failed"):
                AzureCloudSession("azure_exception", "azure", settings)


class TestCloudSessionRealWorldScenarios:
    """Test realistic usage scenarios for cloud sessions."""

    @patch('boto3.session.Session')
    def test_aws_multiple_profile_types(self, mock_boto_session):
        """Test creating AWS sessions with multiple profile types."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        # Key-based authentication
        key_settings = {
            'aws_profile': 'key',
            'aws_region': 'us-east-1',
            'aws_access_key_id': 'AKIAEXAMPLE',
            'aws_secret_access_key': 'secretkey'
        }
        key_session = AWSCloudSession("key_aws", "aws", key_settings)

        # EC2 instance profile
        ec2_settings = {
            'aws_profile': 'ec2',
            'aws_region': 'us-west-2'
        }
        ec2_session = AWSCloudSession("ec2_aws", "aws", ec2_settings)

        # Both should be successful but different instances
        assert key_session.session_available is True
        assert ec2_session.session_available is True
        assert key_session is not ec2_session

        # Verify correct boto3 calls
        assert mock_boto_session.call_count == 2

    @patch('dtPyAppFramework.cloud.azure.CertificateCredential')
    @patch('dtPyAppFramework.cloud.azure.ClientSecretCredential')
    def test_azure_multiple_identity_types(self, mock_client_secret, mock_cert_credential):
        """Test creating Azure sessions with multiple identity types."""
        mock_cert_cred = MagicMock()
        mock_client_cred = MagicMock()
        mock_cert_credential.return_value = mock_cert_cred
        mock_client_secret.return_value = mock_client_cred

        # Certificate-based authentication
        cert_settings = {
            'azure_identity_type': 'certificate',
            'azure_tenant_id': 'tenant-123',
            'azure_client_id': 'client-456',
            'certificate_path': '/cert/path.p12'
        }
        cert_session = AzureCloudSession("cert_azure", "azure", cert_settings)

        # Client secret authentication
        secret_settings = {
            'azure_identity_type': 'key',
            'azure_tenant_id': 'tenant-123',
            'azure_client_id': 'client-789',
            'client_secret': 'secret_value'
        }
        secret_session = AzureCloudSession("secret_azure", "azure", secret_settings)

        # Both should be successful but different instances
        assert cert_session.session_available is True
        assert secret_session.session_available is True
        assert cert_session is not secret_session

        # Verify different Azure credentials were used
        assert cert_session.get_session() is mock_cert_cred
        assert secret_session.get_session() is mock_client_cred

    @patch('dtPyAppFramework.cloud.aws.run_cmd')
    @patch('boto3.session.Session')
    def test_aws_sso_profile_parsing(self, mock_boto_session, mock_run_cmd):
        """Test AWS SSO profile name parsing."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session
        mock_run_cmd.return_value = "Successfully logged into Start URL: https://example.com"

        test_cases = [
            ('sso:dev-profile', 'dev-profile'),
            ('sso:prod-env-profile', 'prod-env-profile'),
            ('sso:my-company-dev', 'my-company-dev')
        ]

        for aws_profile, expected_sso_profile in test_cases:
            settings = {
                'aws_profile': aws_profile,
                'aws_region': 'us-east-1'
            }

            session = AWSCloudSession(f"test_{expected_sso_profile}", "aws", settings)

            # Verify correct SSO profile was extracted
            expected_command = f'aws sso login --profile {expected_sso_profile}'
            mock_run_cmd.assert_any_call(expected_command)
            assert session.session_available is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

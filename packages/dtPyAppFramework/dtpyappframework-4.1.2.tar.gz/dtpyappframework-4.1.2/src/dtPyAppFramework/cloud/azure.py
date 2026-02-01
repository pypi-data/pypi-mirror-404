from .cloud_session import AbstractCloudSession

from azure.identity import CertificateCredential, ClientSecretCredential, InteractiveBrowserCredential
import logging


class AzureCloudSession(AbstractCloudSession):

    def __init__(self, name, session_type, settings):
        super().__init__(name, session_type, settings)

        # Get Azure identity type
        self.azure_identity_type = self.get_setting('azure_identity_type')
        if not self.azure_identity_type:
            logging.error('Missing required azure_identity_type parameter.')
            return

        self.azure_tenant_id = self.get_setting('azure_tenant_id')
        if not self.azure_tenant_id:
            logging.error('Missing required azure_tenant_id parameter.')
            return

        self.azure_session = self.__initialise_session()
        if self.azure_session is None:
            logging.error(f'An Azure Session could not be established for cloud session name "{self.name}".')
        else:
            self.session_available = True
            logging.info(f'Successfully established Azure Session for cloud session name "{self.name}".')

    def __initialise_session(self):
        if self.azure_identity_type == 'certificate':
            azure_client_id = self.get_setting('azure_client_id')
            certificate_path = self.get_setting('certificate_path')
            if not azure_client_id or not certificate_path:
                logging.error('Requires both azure_client_id and certificate_path parameters.')
                return None
            certificate_password = self.get_setting('certificate_password')
            return CertificateCredential(tenant_id=self.azure_tenant_id, client_id=azure_client_id,
                                         certificate_path=certificate_path, password=certificate_password)
        elif self.azure_identity_type == 'key':
            azure_client_id = self.get_setting('azure_client_id')
            client_secret = self.get_setting('client_secret')
            if not azure_client_id or not client_secret:
                logging.error(
                    'Requires both azure_client_id and client_secret parameters.')
                return None
            return ClientSecretCredential(tenant_id=self.azure_tenant_id, client_id=azure_client_id,
                                          client_secret=client_secret)
        elif self.azure_identity_type == 'interactive_browser':
            return InteractiveBrowserCredential(tenant_id=self.azure_tenant_id)
        else:
            logging.error(f"Unrecognised Azure Identity Type {self.azure_identity_type}.")
            return None

    def get_session(self):
        return self.azure_session

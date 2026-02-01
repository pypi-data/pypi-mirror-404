from .cloud_session import AbstractCloudSession
from ..misc import run_cmd

import boto3
import logging


class AWSCloudSession(AbstractCloudSession):

    def __init__(self, name, session_type, settings):
        super().__init__(name, session_type, settings)

        self.aws_profile = self.get_setting('aws_profile')
        if not self.aws_profile:
            logging.error('Missing required aws_profile parameter.')
            return

        self.aws_region = self.get_setting('aws_region')
        if not self.aws_region:
            logging.error('Missing required aws_region parameter.')
            return

        self.aws_session = self.__initialise_session()
        if self.aws_session is None:
            logging.error(f'An AWS Session could not be established for cloud session name "{self.name}".')
        else:
            self.session_available = True
            logging.info(f'Successfully established AWS Session for cloud session name "{self.name}".')

    def __initialise_session(self):
        if self.aws_profile == 'key':
            aws_access_key_id = self.get_setting('aws_access_key_id')
            aws_secret_access_key = self.get_setting('aws_secret_access_key')
            if not aws_access_key_id or not aws_secret_access_key:
                logging.error('Missing either aws_access_key_id and aws_secret_access_key parameters.')
                return None
            return boto3.session.Session(region_name=self.aws_region, aws_access_key_id=aws_access_key_id,
                                         aws_secret_access_key=aws_secret_access_key)
        elif self.aws_profile == 'ec2':
            return boto3.session.Session(region_name=self.aws_region)
        elif self.aws_profile.startswith('sso'):
            aws_sso_profile = self.aws_profile.split(':')[1]
            aws_sso_resp = run_cmd(f'aws sso login --profile {aws_sso_profile}')
            if not aws_sso_resp or "Successfully logged into Start URL" not in aws_sso_resp:
                logging.error(f"Unable to initialise SSO for the AWS profile {aws_sso_profile}.")
                return None
            return boto3.session.Session(region_name=self.aws_region)
        else:
            logging.error(f"Unrecognised AWS Profile type {self.aws_profile}.")
            return None

    def get_session(self):
        return self.aws_session

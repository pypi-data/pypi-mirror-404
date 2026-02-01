from ..decorators import singleton
from ..settings import Settings

from .aws import AWSCloudSession
from .azure import AzureCloudSession

import logging


@singleton()
class CloudSessionManager(object):

    def __init__(self):
        logging.info('Loading Cloud Session Manager')

        defined_sessions = Settings().get('cloud_sessions', [])
        self.sessions = self.__load_sessions(defined_sessions)

    @staticmethod
    def __load_sessions(defined_sessions) -> list:
        sessions = []
        for defined_session in defined_sessions:
            session_type = defined_session["session_type"]
            name = defined_session["name"]
            logging.info(f'Loading session "{name}" or type "{session_type}".')
            if session_type == "aws":
                sessions.append(AWSCloudSession(**defined_session))
            elif session_type == "azure":
                sessions.append(AzureCloudSession(**defined_session))
            else:
                logging.error(f'Unrecognised session type "{session_type}" for session "{name}".')

        return sessions

    def get_session(self, name):
        for session in self.sessions:
            if session.name == name:
                return session.get_session()

        logging.error(f'No Cloud Session with the name "{name}" was found in the defined sessions.')

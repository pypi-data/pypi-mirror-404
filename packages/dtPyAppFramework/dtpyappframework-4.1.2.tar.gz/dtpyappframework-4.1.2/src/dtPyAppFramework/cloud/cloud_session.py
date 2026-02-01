from abc import abstractmethod


class AbstractCloudSession:

    def __init__(self, name, session_type, settings):
        self.name = name
        self.session_type = session_type
        self.settings = settings
        self.session_available = False

    def get_setting(self, key):
        return self.settings.get(key, None)

    @abstractmethod
    def get_session(self):
        raise NotImplementedError

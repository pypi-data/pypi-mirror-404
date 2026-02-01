import platform
import os
import shutil
import logging
import socket
import tempfile

from multiprocessing import current_process
from ..decorators import singleton


@singleton()
class ApplicationPaths(object):
    """
    Singleton class for managing application paths based on the operating system.

    Attributes:
        app_short_name (str): Short name or abbreviation of the application.
        forced_os (str): Forced operating system type.
        spawned_instance (bool): Indicates whether it's a spawned instance.
        auto_create (bool): Automatically create directories if True.
        clean_temp (bool): Clean temporary directory if True.
        forced_dev_mode (bool): Force development mode if True.
        worker_id (int): Worker ID for spawned instances.
    """

    def __init__(self, app_short_name, forced_os=None, forced_dev_mode=False, auto_create=True,
                 clean_temp=True, spawned_instance=False, worker_id=None, *args, **kwargs) -> None:
        super().__init__()
        # Initialization of attributes
        self.app_short_name = app_short_name
        self.forced_os = forced_os
        self.spawned_instance = spawned_instance
        self.auto_create = auto_create
        self.clean_temp = clean_temp
        self.forced_dev_mode = forced_dev_mode
        self.worker_id = worker_id

        # Track which paths were successfully created
        self.path_creation_status = {}

        # Set development mode environment variable
        if self.forced_dev_mode:
            os.environ['DEV_MODE'] = "True"

        # Initialise various paths
        self.logging_root_path = self.__init_logging_root_path()
        self.app_data_root_path = self.__init_app_data_root_path()
        self.usr_data_root_path = self.__init_usr_data_root_path()
        self.tmp_root_path = self.__init_tmp_root_path()

        # Initialise directories
        self.__init_directories()

    def log_paths(self):
        """
        Log the paths for debugging purposes.
        """
        logging.info(f'Logging Root Path: {self.logging_root_path}')
        logging.info(f'Application Data Root Path: {self.app_data_root_path}')
        logging.info(f'User Data Root Path: {self.usr_data_root_path}')
        logging.info(f'Temp Root Path: {self.tmp_root_path}')

    def _safe_makedirs(self, path_name, path_value):
        """
        Attempt to create a directory, logging a warning on failure.

        Args:
            path_name (str): Descriptive name of the path (for status tracking).
            path_value (str): The actual filesystem path to create.

        Returns:
            bool: True if the directory exists after this call, False otherwise.
        """
        try:
            os.makedirs(path_value, exist_ok=True)
            self.path_creation_status[path_name] = True
            return True
        except OSError as ex:
            logging.warning(
                f'Could not create {path_name} directory "{path_value}": {ex}. '
                f'Functionality depending on this path may be unavailable.'
            )
            self.path_creation_status[path_name] = False
            return False

    def is_path_available(self, path_name):
        """
        Check whether a named path was successfully created.

        Args:
            path_name (str): One of 'tmp', 'logging', 'usr_data', 'app_data'.

        Returns:
            bool: True if the path was created successfully, False if creation
                  failed, None if auto_create was not enabled.
        """
        return self.path_creation_status.get(path_name)

    def __init_directories(self):
        """
        Initialise directories based on configuration.

        Directory creation failures are logged as warnings rather than
        raising exceptions, allowing the application to continue with
        reduced functionality when system-level paths are not writable.
        """
        # Clean temporary directory if configured
        if self.clean_temp and os.path.exists(self.tmp_root_path):
            try:
                shutil.rmtree(self.tmp_root_path, ignore_errors=False)
            except OSError as ex:
                logging.warning(
                    f'Could not clean temporary directory "{self.tmp_root_path}": {ex}'
                )

        # Automatically create directories if configured
        if self.auto_create:
            self._safe_makedirs('tmp', self.tmp_root_path)
            self._safe_makedirs('logging', self.logging_root_path)
            self._safe_makedirs('usr_data', self.usr_data_root_path)
            self._safe_makedirs('app_data', self.app_data_root_path)

    def __os(self):
        """
        Get the operating system type.

        Returns:
            str: Operating system type.
        """
        if self.forced_os:
            return self.forced_os
        else:
            return platform.system()

    def _is_root(self):
        """Check if running with root/admin privileges on Unix-like systems."""
        return hasattr(os, 'getuid') and os.getuid() == 0

    def _get_container_identifier(self):
        """
        Get a unique identifier for the current container instance.

        This method attempts to determine the container name from various
        environment variables commonly set in containerised environments.

        The lookup order is:
            1. CONTAINER_NAME - explicitly set container name
            2. POD_NAME - Kubernetes pod name
            3. HOSTNAME - Docker default (usually container ID or custom hostname)
            4. Fallback to socket.gethostname()

        Returns:
            str: Container identifier suitable for use in path names.
        """
        # Check for explicitly set container name
        container_name = os.environ.get('CONTAINER_NAME')
        if container_name:
            return container_name

        # Check for Kubernetes pod name
        pod_name = os.environ.get('POD_NAME')
        if pod_name:
            return pod_name

        # Use HOSTNAME (Docker sets this to container ID by default)
        hostname = os.environ.get('HOSTNAME')
        if hostname:
            return hostname

        # Fallback to socket hostname
        return socket.gethostname()

    def __init_logging_root_path(self):
        """
        Initialise the logging root path based on the operating system.

        In container mode, logs are organised under a container-specific subfolder
        to support multiple containers sharing the same log volume. The structure
        becomes: {base_log_path}/{container_name}/{timestamp}/

        Returns:
            str: Logging root path.
        """
        _path = None
        if os.environ.get("CONTAINER_MODE", None):
            # Container mode: logs organised by container name
            container_id = self._get_container_identifier()
            _path = os.path.join(os.getcwd(), 'logs', container_id)
        elif os.environ.get("DEV_MODE", None):
            _path = os.path.join(os.getcwd(), 'logs')
        elif self.__os() == "Windows":
            _path = os.path.join(os.environ.get("LOCALAPPDATA"), self.app_short_name, 'logs')
        elif self.__os() == "Darwin":
            _path = os.path.join(os.path.expanduser('~/Library/Logs'), self.app_short_name)
        elif self.__os() == "Linux":
            if self._is_root():
                _path = os.path.join('/var/log', self.app_short_name)
            else:
                xdg_state = os.environ.get('XDG_STATE_HOME', os.path.expanduser('~/.local/state'))
                _path = os.path.join(xdg_state, self.app_short_name, 'log')

        if _path is None:
            _path = os.path.join(os.getcwd(), 'logs')

        os.environ['dt_LOGGING_PATH'] = _path
        return _path

    def __init_app_data_root_path(self):
        """
        Initialise the application data root path based on the operating system.

        This path represents system-wide / all-users application data.
        On Linux as root, uses FHS-compliant /var/lib. As a regular user,
        falls back to XDG_CONFIG_HOME.

        Returns:
            str: Application data root path.
        """
        _path = None
        if os.environ.get("CONTAINER_MODE", None):
            _path = os.path.join(os.getcwd(), 'data')
        elif os.environ.get("DEV_MODE", None):
            _path = os.path.join(os.getcwd(), 'data', 'app')
        elif self.__os() == "Windows":
            _path = os.path.join(os.environ.get("ALLUSERSPROFILE"), self.app_short_name)
        elif self.__os() == "Darwin":
            _path = os.path.join('/Library/Application Support', self.app_short_name)
        elif self.__os() == "Linux":
            if self._is_root():
                _path = os.path.join('/var/lib', self.app_short_name)
            else:
                xdg_config = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
                _path = os.path.join(xdg_config, self.app_short_name)

        if _path is None:
            _path = os.path.join(os.getcwd(), 'data', 'app')

        os.environ['dt_APP_DATA'] = _path
        return _path

    def __init_usr_data_root_path(self):
        """
        Initialise the user data root path based on the operating system.

        This path represents the current user's application data.
        On Linux as root (service context), uses /etc for system configuration.
        As a regular user, uses XDG_DATA_HOME for persistent user data.

        Returns:
            str: User data root path.
        """
        _path = None
        if os.environ.get("CONTAINER_MODE", None):
            _path = os.path.join(os.getcwd(), 'data')
        elif os.environ.get("DEV_MODE", None):
            _path = os.path.join(os.getcwd(), 'data', 'usr')
        elif self.__os() == "Windows":
            _path = os.path.join(os.environ.get("APPDATA"), self.app_short_name)
        elif self.__os() == "Darwin":
            _path = os.path.join(os.path.expanduser('~/Library/Application Support'), self.app_short_name)
        elif self.__os() == "Linux":
            if self._is_root():
                _path = os.path.join('/etc', self.app_short_name)
            else:
                xdg_data = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
                _path = os.path.join(xdg_data, self.app_short_name)

        if _path is None:
            _path = os.path.join(os.getcwd(), 'data', 'usr')

        os.environ['dt_USR_DATA'] = _path
        return _path

    def __init_tmp_root_path(self):
        """
        Initialise the temporary root path based on the operating system.

        In container mode, temp directories are organised under a unique folder
        combining the container name and process ID to prevent collisions between
        multiple container instances sharing the same temp volume. The structure
        becomes: {base_temp_path}/{container_name}_{process_id}/

        Returns:
            str: Temporary root path.
        """
        _path = None
        if os.environ.get("CONTAINER_MODE", None):
            container_id = self._get_container_identifier()
            process_id = os.getpid()
            _path = os.path.join(os.getcwd(), 'temp', f'{container_id}_{process_id}')
        elif os.environ.get("DEV_MODE", None):
            _path = os.path.join(os.getcwd(), 'temp')
        elif self.__os() == "Windows":
            _path = os.path.join(os.environ.get("TEMP"), self.app_short_name)
        elif self.__os() == "Darwin":
            _path = os.path.join(os.environ.get("TMPDIR", tempfile.gettempdir()), self.app_short_name)
        elif self.__os() == "Linux":
            _path = os.path.join(tempfile.gettempdir(), self.app_short_name)

        if _path is None:
            _path = os.path.join(tempfile.gettempdir(), self.app_short_name)

        if self.spawned_instance:
            _path = os.path.join(_path, str(self.worker_id))

        os.environ['dt_TMP'] = _path
        return _path

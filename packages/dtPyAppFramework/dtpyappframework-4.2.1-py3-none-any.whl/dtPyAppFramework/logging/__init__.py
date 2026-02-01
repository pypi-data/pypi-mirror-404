# Importing necessary modules
import logging
import logging.config
import os
import shutil
import multiprocessing
from logging import Formatter
from datetime import datetime
import yaml
from colorlog import ColoredFormatter

# Importing custom modules
from ..paths import ApplicationPaths
from ..settings import Settings
from .default_logging import default_config
from logging import Formatter

# Default log format for console and file logging
DEFAULT_FORMATTER = '%(log_color)s%(asctime)s - %(levelname)-8s - %(processName)s.%(process)d - %(threadName)s.%(thread)d - %(module)s.%(funcName)s.%(lineno)-3d - %(message)s%(reset)s'

_LOGGING_CONFIG_FILENAME = "loggingConfig.yaml"


def new_job():
    """
    Generate a new job ID based on the existence of folders.

    Returns:
        int: A new job ID.
    """
    job_exists = True
    root_folder = os.environ['_dt_log_folder']
    job_id = 0
    while job_exists:
        job_id += 1
        job_exists = os.path.exists(f'{root_folder}/job-{job_id}')
        if job_exists:
            ctime = os.stat(f'{root_folder}/job-{job_id}').st_ctime
            now = datetime.now().timestamp()
            if (now - ctime) > 10:
                job_exists = True
            if (now - ctime) <= 10:
                job_exists = False

    return job_id


def get_logging_config(logging_source=None):
    """
    Get the logging configuration from a specified source or the default sources.

    Args:
        logging_source (str): Path to a logging configuration file.

    Returns:
        tuple: A tuple containing the logging source and the logging configuration.
    """
    application_paths = ApplicationPaths()
    config_path = None
    if logging_source and logging_source != "DEFAULT":
        config_path = logging_source
    elif not logging_source:
        for _path in [os.path.join(application_paths.usr_data_root_path, _LOGGING_CONFIG_FILENAME),
                      os.path.join(application_paths.app_data_root_path, _LOGGING_CONFIG_FILENAME),
                      os.path.join(os.getcwd(), "config", _LOGGING_CONFIG_FILENAME)]:
            if os.path.exists(_path):
                config_path = _path
                break

    if config_path:
        return config_path, yaml.safe_load(config_path)
    else:
        return "DEFAULT", default_config(log_level=Settings().get("logging.level", "INFO"),
                                         rotation_backup_count=Settings().get("logging.rotation_backup_count", 5))


def purge_old_logs(log_path, rotation_backup_count):
    if not os.path.isdir(log_path):
        return
    timestamped_dirs = []
    for entry in os.scandir(log_path):
        if entry.is_dir():
            dir_name = entry.name
            try:
                dir_time = datetime.strptime(dir_name, '%Y%m%d_%H%M%S')
                timestamped_dirs.append((entry.path, dir_time))
            except ValueError:
                # If the directory name doesn’t match the timestamp format, skip it
                pass

    timestamped_dirs.sort(key=lambda x: x[1], reverse=True)
    logging.info(f'Keeping on the last "{rotation_backup_count}" log folders.')
    dirs_to_delete = timestamped_dirs[rotation_backup_count:]
    for dir_path, _ in dirs_to_delete:
        logging.warning(f'Deleting old log folder: {dir_path}')
        shutil.rmtree(dir_path, ignore_errors=True)


def initialise_logging(spawned_process=False, job_id=None, worker_id=None, parent_log_path=None):
    """
    Initialize logging configuration based on the environment and application settings.

    Args:
        spawned_process (bool): Indicates if the process is spawned.
        job_id (int): Job ID for the spawned process.
        worker_id (int): Worker ID for the spawned process.
        parent_log_path (str): Path to the parent log folder for spawned processes.

    Returns:
        str or None: The absolute path to the log folder if using default configuration, otherwise None.
    """
    app_paths = ApplicationPaths()
    if spawned_process:
        using_default = bool(os.environ['_dt_using_default'])
        logging_source = os.environ['_dt_logging_config_file']
        logging_source, logging_config = get_logging_config(logging_source)
    else:
        logging_source, logging_config = get_logging_config()
        os.environ['_dt_using_default'] = str(logging_source == "DEFAULT")
        os.environ['_dt_logging_config_file'] = logging_source
        using_default = logging_source == "DEFAULT"

    if using_default:
        # If using default configuration, set up log folder and file names
        if spawned_process:
            log_folder = f'{parent_log_path}/job-{job_id}/{worker_id}'
        else:
            if os.path.isdir(app_paths.logging_root_path):
                purge_old_logs(app_paths.logging_root_path, Settings().get("logging.rotation_backup_count", 5))
            else:
                logging.warning(
                    f'Logging directory "{app_paths.logging_root_path}" does not exist; '
                    f'skipping log purge.'
                )
            log_folder = f'{app_paths.logging_root_path}/{format(datetime.now().strftime("%Y%m%d_%H%M%S"))}'

        try:
            os.makedirs(log_folder, exist_ok=True)
        except OSError as ex:
            logging.warning(
                f'Could not create log folder "{log_folder}": {ex}. '
                f'File logging will be unavailable.'
            )
            return None
        # Set file names based on log levels
        logging_config['handlers']['logfile_ALL']['filename'] = '{}/info-{}.log'.format(log_folder,
                                                                                        app_paths.app_short_name)
        logging_config['handlers']['logfile_ERR']['filename'] = '{}/error-{}.log'.format(log_folder,
                                                                                         app_paths.app_short_name)

        logging.config.dictConfig(logging_config)

        if Settings().get("logging.log_to_console", False):
            # Configure console logging
            formatter = ColoredFormatter(DEFAULT_FORMATTER)

            console_stream = logging.StreamHandler()
            console_stream.setLevel(logging.DEBUG)
            console_stream.setFormatter(formatter)
            console_stream.name = 'console_ALL'

            logging.getLogger().addHandler(console_stream)
            logging.getLogger("defaultLogger").addHandler(console_stream)

            logging.getLogger('console').addHandler(console_stream)
            logging.getLogger('console').debug('Logging configuration read from: {}'.format(logging_source))

        return os.path.abspath(log_folder)

    else:
        # If not using default configuration, apply the provided logging configuration
        logging.config.dictConfig(logging_config)
        logging.debug('Logging configuration read from: {}'.format(logging_source))
        return None
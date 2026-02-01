from ..decorators import singleton
from .. import logging as app_logging
from .. import paths
from .. import settings
from .. import resources

from InquirerPy import prompt
from InquirerPy import inquirer

from multiprocessing import current_process
from argparse import ArgumentParser
from .multiprocessing import MultiProcessingManager
import platform
import sys
import os
import logging
import base64
import threading
import signal
import time

if platform.system() == "Windows":
    try:
        from dtPyAppFramework.process.windows_service import call_service
    except ImportError as ex:
        logging.error("pywin32 is not installed.")
        raise ex


def is_multiprocess_spawned_instance():
    """
    Check if the current process is a spawned instance in a multiprocessing environment.

    Returns:
        bool: True if the process is a spawned instance, False otherwise.
    """
    return current_process().name != "MainProcess" or '--multiprocessing-fork' in sys.argv


@singleton()
class ProcessManager():
    """
    Singleton class for managing the initialization and execution of a multiprocessing-enabled application.

    Attributes:
        description (str): Application description.
        version (str): Application version.
        short_name (str): Short name or abbreviation of the application.
        full_name (str): Full name of the application.
        console_app (bool): True if the application is a console app, False otherwise.
        main_procedure (callable): Main procedure to be executed.
        application_paths (ApplicationPaths): Object managing application paths.
        application_settings (Settings): Object managing application settings.
        secrets_manager (SecretsManager): Object managing secrets.
        resource_manager (ResourceManager): Object managing application resources.
        log_path (str): Path to the log folder.
        multiprocessing_manager (MultiProcessingManager): Manager for multiprocessing functionality.
        stdout_txt_file (file): File object for capturing stdout to a text file.
        stderr_txt_file (file): File object for capturing stderr to a text file.
    """

    def __init__(self, description, version, short_name, full_name, console_app, main_procedure, exit_procedure=None):
        super().__init__()
        # Initialization of attributes
        self.description = description
        self.version = version
        self.short_name = short_name
        self.full_name = full_name
        self.console_app = console_app
        self.application_paths = None
        self.application_settings = None
        self.secrets_manager = None
        self.resource_manager = None
        self.log_path = None
        self.main_procedure = main_procedure
        self.exit_procedure = exit_procedure
        self.multiprocessing_manager = None
        self.stdout_txt_file = None
        self.stderr_txt_file = None
        self.running = threading.Event()
        self.spawned_running_event = None
        self._shutdown_requested = False  # Track if shutdown was explicitly requested
        self._waiting_for_shutdown = False  # Track if app called wait_for_shutdown()

    def __initialise_spawned_application__(self, parent_log_path, job_id, worker_id, job_name, running_event):
        """
        Initialize a spawned instance of the application in a multiprocessing environment.

        Args:
            parent_log_path (str): Path to the parent log folder for spawned processes.
            job_id (int): Job ID for the spawned process.
            worker_id (int): Worker ID for the spawned process.
            job_name (str): Name of the spawned job.
            running_event (threading.Event): Event to signal process shutdown.
        """
        try:
            if is_multiprocess_spawned_instance():
                self.spawned_running_event = running_event
                self.application_paths = paths.ApplicationPaths(app_short_name=self.short_name,
                                                                spawned_instance=True, worker_id=worker_id)
                self.application_settings = settings.Settings(application_paths=self.application_paths,
                                                              app_short_name=self.short_name)
                self.resource_manager = resources.ResourceManager(application_paths=self.application_paths)
                self.log_path = app_logging.initialise_logging(spawned_process=True,
                                                               job_id=job_id, worker_id=worker_id,
                                                               parent_log_path=parent_log_path)
                self.application_settings.init_settings_readers()
                self.application_settings.secret_manager.load_cloud_stores()

                from dtPyAppFramework.app_context import AppContext
                AppContext(
                    version=self.version,
                    full_name=self.full_name,
                    short_name=self.short_name,
                    description=self.description,
                )

                self.__initialise_stdout_capt__()

                header_message = f'SPAWNED PROCESS --- {self.full_name} ({self.short_name}), ' \
                                 f'Version: {self.version}. '
                logging.info(header_message)
                print(header_message)

                self.load_config()


        except Exception as ex:
            logging.exception(ex)
            if not self.console_app:
                self.stdout_txt_file.close()
                self.stderr_txt_file.close()

    def __initialise_stdout_capt__(self):
        """
        Initialize capturing of stdout to a text file.
        """
        if not self.console_app:
            stdout_txt = '{}/stdout.txt'.format(self.log_path)
            stderr_txt = '{}/stderr.txt'.format(self.log_path)

            self.stdout_txt_file = open(stdout_txt, mode='w', buffering=1)
            self.stderr_txt_file = open(stderr_txt, mode='w', buffering=1)
            sys.stdout = self.stdout_txt_file
            sys.stderr = self.stderr_txt_file

    def initialise_application(self, arg_parser):
        """
        Initialize the application based on command-line arguments.

        Args:
            arg_parser (ArgumentParser): Command-line argument parser.
        """
        self.multiprocessing_manager = MultiProcessingManager()
        try:
            if not is_multiprocess_spawned_instance():
                self.application_paths = paths.ApplicationPaths(app_short_name=self.short_name)
                self.application_settings = settings.Settings(application_paths=self.application_paths)
                self.application_settings.init_settings_readers()
                self.resource_manager = resources.ResourceManager(application_paths=self.application_paths)
                self.log_path = app_logging.initialise_logging()
                #self.application_settings.init_settings_readers()
                self.application_settings.secret_manager.load_cloud_stores()

                from dtPyAppFramework.app_context import AppContext
                AppContext(
                    version=self.version,
                    full_name=self.full_name,
                    short_name=self.short_name,
                    description=self.description,
                )

                self.__initialise_stdout_capt__()

                header_message = f'{self.full_name} ({self.short_name}), ' \
                                 f'Version: {self.version}. Process ID: {os.getpid()}'
                logging.info(header_message)
                print(header_message)
                if self.log_path is not None:
                    print(f'Log Path: {self.log_path}')
                    self.multiprocessing_manager.set_log_path(self.log_path)
                args = arg_parser.parse_args()

                if args.add_secret:
                    self.__add_secret__(args)
                elif args.service:
                    if platform.system() == "Windows":
                        sys.argv = [sys.argv[0]]
                        call_service(svc_name=self.short_name, svc_display_name=self.full_name,
                                     svc_description=self.description, main_function=self.__main__,
                                     exit_function=self.call_shutdown)

                else:
                    signal.signal(signal.SIGINT, self.request_shutdown)
                    signal.signal(signal.SIGTERM, self.request_shutdown)
                    self.__main__(args)

        except KeyboardInterrupt:
            logging.warning('(KeyboardInterrupt) Exiting application.')
        except Exception as ex:
            logging.exception(str(ex))

    def load_config(self):
        """
        Load configuration settings for the application.
        """
        if not is_multiprocess_spawned_instance():
            self.application_paths.log_paths()

    def _add_secret_file(self, secret_name, file_path, store_as):
        print(f'Adding secret "{secret_name}" from file "{file_path}" as {store_as} ...')
        if not os.path.exists(file_path):
            print(f'The file "{file_path}" could not be found.')
            raise FileNotFoundError(f'The file "{file_path}" could not be found.')

        if store_as.lower() == 'raw':
            with open(file_path, 'r') as file:
                file_content = file.read()
            value = file_content
        elif store_as.lower() == 'base64':
            with open(file_path, 'rb') as file:
                file_content = file.read()
            value = base64.b64encode(file_content).decode('utf-8')
        else:
            raise ValueError(f'Invalid store_as value: {store_as}')

        settings.SecretsManager().set_secret(secret_name, value)
        logging.info(f'Added secret "{secret_name}" to Secret Store.')

    def _prompt_secret_details(self, secret_name):
        """Prompt the user for secret type and value, then store the secret.

        Presents an interactive prompt asking whether the secret is a file or
        a direct value, collects the appropriate input, and persists it.

        Args:
            secret_name (str): The name under which the secret will be stored.
        """
        questions = [
            {
                "type": "rawlist",
                "message": "What form of secret do you wish to add?",
                "default": 2,
                "choices": ["File", "Value"],
                "name": "secret_type",
                "mandatory": True
            },
            {
                "type": "list",
                "message": "Add file as:",
                "choices": ["Raw", "Base64"],
                "name": "file_format",
                "when": lambda result: 'File' in result["secret_type"],
                "mandatory": True
            }
        ]

        result = prompt(questions=questions)
        if result["secret_type"] == "Value":
            result["value"] = inquirer.secret(
                message="Enter Secret Value:",
                transformer=lambda _: "[hidden]", mandatory=True
            ).execute()
        else:
            result["file_path"] = inquirer.text(message="Path to file:", mandatory=True).execute()

        if result["secret_type"] == "File":
            self._add_secret_file(secret_name=secret_name,
                                  file_path=result["file_path"], store_as=result["file_format"])
        else:
            settings.SecretsManager().set_secret(secret_name, result["value"])
            logging.info(f'Added secret "{secret_name}" to Secret Store.')

    def _add_secret_interactive(self):
        """Run the fully interactive secret-addition loop.

        Prompts the user for all secret details (name, type, and value) in a
        loop, allowing multiple secrets to be added in a single session.
        """
        while True:
            questions = [
                {
                    "type": "input",
                    "message": "Enter the secret name:",
                    "instruction": "my-secret-name",
                    "name": "secret_name",
                    "mandatory": True
                },
                {
                    "type": "rawlist",
                    "message": "What form of secret do you wish to add?",
                    "default": 2,
                    "choices": ["File", "Value"],
                    "name": "secret_type",
                    "mandatory": True
                },
                {
                    "type": "list",
                    "message": "Add file as:",
                    "choices": ["Raw", "Base64"],
                    "name": "file_format",
                    "when": lambda result: 'File' in result["secret_type"],
                    "mandatory": True
                }
            ]

            result = prompt(questions=questions)
            if result["secret_type"] == "Value":
                result["value"] = inquirer.secret(
                    message="Enter Secret Value:",
                    transformer=lambda _: "[hidden]", mandatory=True
                ).execute()
            else:
                result["file_path"] = inquirer.text(message="Path to file:", mandatory=True).execute()

            if result["secret_type"] == "File":
                self._add_secret_file(secret_name=result["secret_name"],
                                      file_path=result["file_path"], store_as=result["file_format"])
            else:
                settings.SecretsManager().set_secret(result["secret_name"], result["value"])
                logging.info(f'Added secret "{result["secret_name"]}" to Secret Store.')

            if not inquirer.confirm(message="Do you wish to add another secret?", default=False).execute():
                break

    def _add_secret_with_name(self, args):
        """Handle the name-only mode where the secret name is provided via args.

        Prompts the user for the secret type and value interactively, using the
        name already supplied through command-line arguments.

        Args:
            args: Parsed command-line arguments containing the secret name.
        """
        self._prompt_secret_details(args.name)

    def __add_secret__(self, args):
        """Dispatch secret addition to the appropriate handler based on supplied arguments.

        Supports four modes of operation:
        - No arguments: fully interactive prompting loop.
        - Name only: prompts for type and value.
        - Value only: stores the value directly.
        - File only: reads and stores from a file path.

        Args:
            args: Parsed command-line arguments.
        """
        try:
            name_passed = args.name is not None
            value_passed = args.value is not None
            file_passed = args.file is not None

            if not name_passed and not value_passed and not file_passed:
                self._add_secret_interactive()

            if name_passed and not value_passed and not file_passed:
                self._add_secret_with_name(args)

            if not name_passed and value_passed and not file_passed:
                settings.SecretsManager().set_secret(args.name, args.value)
                logging.info(f'Added secret "{args.name}" to Secret Store.')

            if not name_passed and not value_passed and file_passed:
                self._add_secret_file(args.name, args.file, args.store_as)

        except Exception as ex:
            print(ex)
            logging.error(f'Error occurred while adding secret {args.name}.  Error: {str(ex)}')
            raise ex
        settings.Settings().close()

    def handle_shutdown(self):
        """
        Perform shutdown cleanup operations.

        This method is called automatically when the application exits.
        It executes the exit_procedure callback and closes stdout/stderr capture files.

        Note:
            For most applications, you should not call this directly.
            Use request_shutdown() to signal the application to stop, or
            simply return from your main() method for one-shot applications.
        """
        if self.exit_procedure:
            self.exit_procedure()
        if not self.console_app:
            if self.stdout_txt_file:
                self.stdout_txt_file.close()
            if self.stderr_txt_file:
                self.stderr_txt_file.close()

    def request_shutdown(self, signum=None, frame=None):
        """
        Request the application to shut down gracefully.

        This method signals the application to exit its main loop.
        Use this for long-running applications that called wait_for_shutdown().

        Args:
            signum: Signal number (optional, used by signal handlers).
            frame: Current stack frame (optional, used by signal handlers).

        Example:
            # In your main method for a long-running app:
            def main(self, args):
                # Start background tasks
                self.start_workers()
                # Wait for shutdown signal
                ProcessManager().wait_for_shutdown()

            # From elsewhere (e.g., a REST endpoint):
            ProcessManager().request_shutdown()
        """
        logging.info('Shutdown requested')
        self._shutdown_requested = True
        self.running.clear()

    def call_shutdown(self, signum=None, frame=None):
        """
        Alias for request_shutdown() for backward compatibility.

        Deprecated:
            Use request_shutdown() instead for clarity.
        """
        self.request_shutdown(signum, frame)

    def wait_for_shutdown(self, check_interval: float = 0.5):
        """
        Block until a shutdown signal is received.

        Use this method in long-running applications (daemons, services) that need
        to keep running until explicitly stopped. For one-shot applications that
        complete their work and exit, simply return from your main() method.

        Args:
            check_interval: How often to check for shutdown signal (seconds).
                           Default is 0.5 seconds.

        Example:
            class MyDaemon(AbstractApp):
                def main(self, args):
                    # Start your background services
                    self.start_http_server()
                    self.start_worker_threads()

                    # Block until shutdown is requested
                    ProcessManager().wait_for_shutdown()

                    # Cleanup happens automatically after this returns
        """
        self._waiting_for_shutdown = True
        logging.info('Application waiting for shutdown signal...')

        while self.running.is_set():
            time.sleep(check_interval)

        logging.info('Shutdown signal received, proceeding with cleanup')

    def __main__(self, args):
        """
        Execute the main procedure of the application.

        This method handles two application patterns:

        1. One-shot applications: main() does its work and returns.
           The application exits automatically after main() completes.

        2. Long-running applications: main() calls wait_for_shutdown()
           to block until a shutdown signal is received.

        Args:
            args: Parsed command-line arguments.
        """
        logging.info('Starting application...')
        self.running.set()
        self.load_config()

        logging.debug('Executing main procedure')
        self.main_procedure(args)

        # If the app didn't explicitly wait for shutdown, it's a one-shot app
        # that has completed its work - proceed directly to cleanup
        if not self._waiting_for_shutdown:
            logging.debug('Main procedure completed (one-shot mode)')
            # Only wait if running is still set AND shutdown wasn't requested
            # This handles the case where main() called request_shutdown()
            if self.running.is_set() and not self._shutdown_requested:
                logging.debug('Auto-initiating shutdown for one-shot application')
                self.running.clear()

        self.handle_shutdown()
        logging.info('Application shutdown complete')



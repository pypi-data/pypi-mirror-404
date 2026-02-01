import argparse
import logging
import os
import sys

import psutil
import traceback

from multiprocessing import current_process
from argparse import ArgumentParser
from contextlib import redirect_stdout, redirect_stderr

# Importing modules from the same package
from . import logging as app_logging
from . import paths
from . import settings
from . import resources
from .decorators import singleton
from .process import ProcessManager


class AbstractApp(object):
    """
    An abstract base class for creating applications.

    Attributes:
        app_spec (dict): A dictionary containing application information.
        console_app (bool): Indicates whether the application is a console application.
        process_manager (ProcessManager): Manages the application process.
    """

    def __init__(self, description=None, version=None, short_name=None,
                 full_name=None, console_app=True) -> None:
        """
        Initialise the AbstractApp.

        If any metadata parameter is not provided, the framework attempts to
        auto-discover the value from a corresponding text file in the
        subclass's top-level package directory:

        * ``_description.txt``
        * ``_version.txt``
        * ``_short_name.txt``
        * ``_full_name.txt``

        Args:
            description (str, optional): A short description of the application.
            version (str, optional): The version of the application.
            short_name (str, optional): Short name or abbreviation of the application.
            full_name (str, optional): Full name of the application.
            console_app (bool, optional): Indicates whether the application is a console application (default is True).

        Raises:
            ValueError: If any metadata value is missing after both explicit
                arguments and file-based discovery.
        """
        # Auto-discover missing metadata from text files
        if any(v is None for v in [description, version, short_name, full_name]):
            discovered = self._discover_metadata()
            description = description or discovered.get('description')
            version = version or discovered.get('version')
            short_name = short_name or discovered.get('short_name')
            full_name = full_name or discovered.get('full_name')

        # Validate all metadata is present
        missing = [
            name for name, value in [
                ('description', description),
                ('version', version),
                ('short_name', short_name),
                ('full_name', full_name),
            ]
            if not value
        ]
        if missing:
            raise ValueError(
                f'Missing required application metadata: {", ".join(missing)}. '
                f'Provide them as constructor arguments or create the corresponding '
                f'text files (_version.txt, _full_name.txt, _short_name.txt, '
                f'_description.txt) in your package directory.'
            )

        self.app_spec = {
            'description': description,
            'version': version,
            'short_name': short_name,
            'full_name': full_name,
        }

        self.console_app = console_app or ('--console' in sys.argv)
        # Note: '-c' is now reserved for --container mode
        self.process_manager = None
        super().__init__()

    def _discover_metadata(self):
        """
        Discover application metadata from text files in the subclass's
        top-level package directory.

        Looks for ``_version.txt``, ``_full_name.txt``, ``_short_name.txt``,
        and ``_description.txt`` in the directory containing the subclass's
        top-level package ``__init__.py``.

        Returns:
            dict: Mapping of metadata key to value for each file found.
        """
        import importlib

        metadata = {}
        file_map = {
            'version': '_version.txt',
            'full_name': '_full_name.txt',
            'short_name': '_short_name.txt',
            'description': '_description.txt',
        }

        try:
            subclass_module = type(self).__module__
            top_package_name = subclass_module.split('.')[0]
            top_package = importlib.import_module(top_package_name)
            package_dir = os.path.dirname(os.path.abspath(top_package.__file__))

            for key, filename in file_map.items():
                filepath = os.path.join(package_dir, filename)
                if os.path.isfile(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        metadata[key] = f.read().strip()
        except Exception as ex:
            logging.debug(f'Metadata auto-discovery failed: {ex}')

        return metadata

    @property
    def version(self) -> str:
        """Get the version of the application."""
        return self.app_spec["version"]

    @property
    def description(self) -> str:
        """Get the description of the application."""
        return self.app_spec["description"]

    @property
    def short_name(self) -> str:
        """Get the short name of the application."""
        return self.app_spec["short_name"]

    @property
    def full_name(self) -> str:
        """Get the full name of the application."""
        return self.app_spec["full_name"]

    def define_args(self, arg_parser: ArgumentParser):
        """
        Define command-line arguments for the application.

        Args:
            arg_parser (ArgumentParser): The ArgumentParser object for defining command-line arguments.
        """
        raise NotImplementedError

    def main(self, args):
        """
        The main procedure of the application.

        Args:
            args: Command-line arguments passed to the application.
        """
        raise NotImplementedError

    def exiting(self):
        raise NotImplementedError

    def __define_args(self, arg_parser: ArgumentParser):
        """
        Define command-line arguments based on application state.

        Args:
            arg_parser (ArgumentParser): The ArgumentParser object for defining command-line arguments.
        """
        # Common arguments for various states
        arg_parser.add_argument('--init', action='store_true', required=False, help='Initialise environment')
        arg_parser.add_argument('--add_secret', action='store_true', required=False, help='Add secret to store')
        arg_parser.add_argument('--run', action='store_true', required=False, help='Run Processor')
        arg_parser.add_argument('--service', action='store_true', required=False, help='Run as Service')
        arg_parser.add_argument('--console', action='store_true', required=False, help='Output to Console')
        arg_parser.add_argument('--container', '-c', action='store_true', required=False, help='Enable container mode with simplified directory structure')
        arg_parser.add_argument('--single_folder', action='store_true', required=False, help='Keeps all Directories in a single folder')
        arg_parser.add_argument('--working_dir', action='store', type=str, required=False, help="Sets the Working Directory")
        arg_parser.add_argument('--password', '-p', action='store', type=str, required=False,
                                help="Keystore password. Sets KEYSTORE_PASSWORD environment variable. "
                                     "Required for container deployments with shared keystores.")

        self.define_args(arg_parser)
        # Check specific states and add corresponding arguments
        opts, _ = arg_parser.parse_known_args()

        if opts.working_dir:
            os.chdir(opts.working_dir)

        if opts.single_folder:
            os.environ['DEV_MODE'] = "True"

        # Set container mode based on command line argument or environment variable
        if opts.container or os.environ.get('CONTAINER_MODE', '').lower() in ('true', '1', 'yes'):
            os.environ['CONTAINER_MODE'] = "True"

        # Set keystore password from command line argument (if not already set via environment)
        if opts.password:
            os.environ['KEYSTORE_PASSWORD'] = opts.password
            logging.debug("KEYSTORE_PASSWORD set from --password argument")

        if opts.service:
            arg_parser.add_argument('--install', action='store_true')
        elif opts.add_secret:
            arg_parser.add_argument('--name', action='store', type=str, required=False, help="Secret Name")

            group = arg_parser.add_mutually_exclusive_group(required=False)
            group.add_argument('--value', action='store', type=str, help="Secret Value")
            group.add_argument('--file', action='store', type=str, help="File to add to secret")

            arg_parser.add_argument('--store_as', action='store', type=str, default='raw', choices=['raw', 'base64'],
                                    help="Store file as either base64 or raw")

    def exit(self):
        self.exiting()
        from dtPyAppFramework.settings import Settings
        Settings().close()

    def run(self):
        """
        Run the application.
        """
        arg_parser = argparse.ArgumentParser(prog=self.app_spec["short_name"], description=self.app_spec["description"])
        self.__define_args(arg_parser)
        self.process_manager = ProcessManager(description=self.description, version=self.version,
                                              short_name=self.short_name, full_name=self.full_name,
                                              console_app=self.console_app, main_procedure=self.main,
                                              exit_procedure=self.exit)
        self.process_manager.initialise_application(arg_parser)

from ..paths import ApplicationPaths
from ..decorators import singleton

import os
import logging


@singleton()
class ResourceManager(object):
    """
    Singleton class for managing resources within the application.

    Attributes:
        application_paths (ApplicationPaths): Object managing application paths.
        resource_paths (list): List of paths where resources can be located.
    """

    def __init__(self, application_paths=None) -> None:
        """
        Initialize ResourceManager.

        Args:
            application_paths (ApplicationPaths, optional): Object managing application paths.
        """
        super().__init__()
        self.application_paths = application_paths
        if not self.application_paths:
            self.application_paths = ApplicationPaths()
        self.resource_paths = self.__load_default_paths__()
        self._sort_paths()

    def _sort_paths(self):
        self.resource_paths.sort(key=lambda x: x[1])

    def __load_default_paths__(self):
        """
        Load default resource paths.

        Returns:
            list: List of default resource paths.
        """
        return [(os.path.join(self.application_paths.usr_data_root_path, "resources"), 100),
                (os.path.join(self.application_paths.app_data_root_path, "resources"), 200),
                (os.path.join(os.getcwd(), "resources"), 300)]

    def add_resource_path(self, path, priority=10):
        """
        Add a custom resource path.

        Args:
            path (str): Path to be added to the resource paths.
            priority (int): The priority of the path when doing lookups. Lower the number, the higher the priority.
        """
        self.resource_paths.append((path, priority))
        self._sort_paths()

    def remove_resource_path(self, path):
        """
        Remove a custom resource path.

        Args:
            path (str): Path to be removed from the resource paths.
        """
        p_to_remove = None
        for p in self.resource_paths:
            if p[0] == path:
                p_to_remove = p
                break

        if p_to_remove is not None:
            self.resource_paths.remove(p_to_remove)

    def get_resource_path(self, resource):
        """
        Get the full path to a resource.

        Args:
            resource (str): Name of the resource.

        Returns:
            str: Full path to the resource, or None if not found.
        """
        for path in self.resource_paths:
            if os.path.exists(os.path.join(path[0], resource)):
                logging.info(f'Returning resource from: "{os.path.join(path[0], resource)}"')
                return os.path.join(path[0], resource)

        logging.error(f'Resource: "{resource}" could not be found')
        return None

    def save_resource(self, resource_name, content):
        """
        Save content to a resource file.

        Args:
            resource_name (str): Name of the resource file.
            content (str): Content to save to the resource file.

        Returns:
            str: Path to the saved resource file, or None if failed.
        """
        # Use the first resource path with highest priority for saving
        if not self.resource_paths:
            logging.error("No resource paths configured")
            return None
            
        save_path = self.resource_paths[0][0]  # First path (highest priority)
        
        # Ensure the directory exists
        os.makedirs(save_path, exist_ok=True)
        
        full_path = os.path.join(save_path, resource_name)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f'Resource saved to: "{full_path}"')
            return full_path
        except Exception as e:
            logging.error(f'Failed to save resource "{resource_name}": {e}')
            return None

    def load_resource(self, resource_name):
        """
        Load content from a resource file.

        Args:
            resource_name (str): Name of the resource file.

        Returns:
            str: Content of the resource file, or None if not found.
        """
        resource_path = self.get_resource_path(resource_name)
        if not resource_path:
            return None
            
        try:
            with open(resource_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logging.info(f'Resource loaded from: "{resource_path}"')
            return content
        except Exception as e:
            logging.error(f'Failed to load resource "{resource_name}": {e}')
            return None

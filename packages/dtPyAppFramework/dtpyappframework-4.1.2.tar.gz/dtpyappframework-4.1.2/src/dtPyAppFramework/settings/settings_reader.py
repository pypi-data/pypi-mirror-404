from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import yaml
import logging
import os
import hashlib

class ConfigFileWatcher(FileSystemEventHandler):

    def __init__(self, change_action, delete_action, watch_file, watch_folder):
        self.change_action = change_action
        self.delete_action = delete_action
        self.watch_file = watch_file
        self.watch_folder = watch_folder
        self.watch_file_sha256 = self.calculate_sha256(os.path.join(self.watch_folder, self.watch_file))

    def calculate_sha256(self, file_path):
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read and update hash in chunks of 4K
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except FileNotFoundError:
            return "File not found."
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def process(self, event: FileSystemEvent):
        """
           event.event_type
               'modified' | 'created' | 'moved' | 'deleted'
           event.src_path
               path to the modified file
           """
        if event.src_path.endswith(self.watch_file):
            if event.event_type == 'deleted':
                logging.warning(f'Config Watch File Deleted: {event.src_path}')
                self.delete_action()
            elif event.event_type == 'modified':
                new_sha256 = self.calculate_sha256(event.src_path)
                if new_sha256 != self.watch_file_sha256:
                    logging.warning(f'Config Watch File Changed: {event.src_path} - WAS: {self.watch_file_sha256},'
                                    f' NOW: {new_sha256}')
                    self.watch_file_sha256 = new_sha256
                    self.change_action()
            elif event.event_type == 'created':
                logging.warning(f'Config Watch File Created: {event.src_path}')
                self.watch_file_sha256 = self.calculate_sha256(event.src_path)
                self.change_action()


    def on_deleted(self, event: FileSystemEvent) -> None:
        self.process(event)

    def on_modified(self, event: FileSystemEvent):
        self.process(event)

    def on_created(self, event: FileSystemEvent):
        self.process(event)



class SettingsReader(dict):
    """
    A class for reading settings from a YAML file and accessing them using dot notation.

    Attributes:
        path (str): Path to the directory containing the settings YAML file.
        priority (int): Priority of the settings reader.
        settings_file (str): Full path to the settings YAML file.
    """
    CONFIG_FILE = "config.yaml"


    def __init__(self, path: str, priority: int) -> None:
        """
        Initialize the SettingsReader.

        Args:
            path (str): Path to the directory containing the settings YAML file.
            priority (int): Priority of the settings reader.
        """
        self.priority = priority
        self.settings_file = os.path.join(path, self.CONFIG_FILE)

        self.load_yaml_file()
        self.observer = Observer()
        event_handler = ConfigFileWatcher(change_action=self.load_yaml_file, delete_action=super().clear,
                                          watch_file=self.CONFIG_FILE, watch_folder=path)
        self.observer.schedule(event_handler, path, recursive=False)
        if os.path.exists(path):
            self.observer.start()

        super().__init__()

    def load_yaml_file(self):
        """
        Load settings from the YAML file and update the dictionary.
        """
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='UTF-8') as file:
                    super().clear()
                    self.update(yaml.safe_load(file))
                logging.info(f'Loaded settings file {self.settings_file}.')
            except Exception as ex:
                logging.error(f'Error reading in settings file {self.settings_file}. {str(ex)}')
                print(f'Error reading in settings file {self.settings_file}. {str(ex)}')
        else:
            logging.warning(f'Settings file "{self.settings_file}" does not exist.')

    def clear(self) -> None:
        """
        Clear method not implemented.
        """
        raise NotImplementedError

    def popitem(self):
        """
        popitem method not implemented.
        """
        raise NotImplementedError

    def __setitem__(self, k, v) -> None:
        """
        __setitem__ method not implemented.
        """
        raise NotImplementedError

    def pop(self, __key):
        """
        pop method not implemented.
        """
        raise NotImplementedError

    def __getitem__(self, key):
        """
        Get item from the dictionary using dot notation.

        Args:
            key (str): Key in dot notation.

        Returns:
            The value associated with the key.
        """
        keys = key.split('.')
        if len(keys) == 1:
            return dict.__getitem__(self, key)
        else:
            data = self.copy()
            for key in keys:
                if key in data:
                    data = data[key]
                else:
                    return None
            return data

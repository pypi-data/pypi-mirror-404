import os

from dtPyAppFramework.misc.yaml import load_yaml_with_files


class ModulePackage:

    def __init__(self, data):
        for required_key in ['version', 'short_name', 'full_name', 'description']:
            if required_key not in data:
                raise NotImplementedError(f'The required key "{required_key}" was not found in the module Metadata.')
        self.data = data

    @property
    def version(self):
        return self.data.get('version')

    @property
    def short_name(self):
        return self.data.get('short_name')

    @property
    def full_name(self):
        return self.data.get('full_name')

    @property
    def description(self):
        return self.data.get('description')

    @property
    def copyright(self):
        return self.data.get('copyright')

    @property
    def licence(self):
        return self.data.get('licence')


def load_module_package(metadata_file_path):
    if not os.path.exists(metadata_file_path):
        raise FileNotFoundError(f'The Metadata file "{metadata_file_path}" was not found.')
    return ModulePackage(load_yaml_with_files(yaml_path=metadata_file_path))

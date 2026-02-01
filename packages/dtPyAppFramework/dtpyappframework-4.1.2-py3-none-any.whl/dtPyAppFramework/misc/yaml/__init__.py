import os
import yaml


class YamlFileLoader(yaml.SafeLoader):
    """ Custom YAML Loader to handle !file tag """

    def __init__(self, stream, base_path=None):
        super().__init__(stream)
        self._base_path = base_path


def file_constructor(loader, node):
    """ Custom constructor for !file tag in YAML """
    file_path = loader.construct_scalar(node)

    # Get the base path from the loader
    base_path = loader._base_path or ""

    # Construct full path to the referenced file
    full_path = os.path.join(base_path, file_path)

    # Read the file content
    with open(full_path, 'r') as f:
        return f.read()


yaml.add_constructor('!file', file_constructor, YamlFileLoader)


def load_yaml_with_files(yaml_path):
    """ Load a YAML file and resolve !file references """

    base_path = os.path.dirname(yaml_path)  # Get the directory of the YAML file

    with open(yaml_path, 'r') as yaml_file:
        # Load the YAML file with the custom loader and pass the base path
        data = yaml.load(yaml_file, Loader=lambda stream: YamlFileLoader(stream, base_path))

    return data

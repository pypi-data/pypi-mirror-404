import os

from dtPyAppFramework.misc.packaging import load_module_package, ModulePackage

dir_path = os.path.dirname(os.path.realpath(__file__))
module_package: ModulePackage = load_module_package(os.path.join(dir_path, '_metadata.yaml'))


def version():
    """Returns the version of the module."""
    return module_package.version


from dtPyAppFramework.app_context import AppContext

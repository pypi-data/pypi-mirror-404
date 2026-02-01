import importlib
import pkgutil
from abc import ABC

from keneth.di_contracts import ServiceInterface


class ClassResolver(ServiceInterface):
    def __init__(self):
        self.modules = []

    def __load_module__(self, package):
        for finder, module_name, is_pkg in pkgutil.walk_packages(
            package.__path__, package.__name__ + "."
        ):
            module = importlib.import_module(module_name)
            self.modules.append(module)

    def load_modules(self, packages):
        for package in packages:
            self.__load_module__(package)

    def resolve(self, base_class: ABC) -> list[ABC]:
        subclasses = []
        for module in self.modules:
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if (
                    isinstance(attribute, type)
                    and issubclass(attribute, base_class)
                    and attribute is not base_class
                ):
                    subclasses.append(attribute)
        return subclasses

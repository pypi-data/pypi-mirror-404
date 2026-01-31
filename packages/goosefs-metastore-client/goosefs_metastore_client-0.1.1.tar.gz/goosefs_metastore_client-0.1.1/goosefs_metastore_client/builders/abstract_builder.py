"""Abstract builder for GooseFS objects."""
from abc import ABC, abstractmethod


class AbstractBuilder(ABC):
    """Abstract builder class to be inherited by other builders."""

    @abstractmethod
    def build(self):
        """
        Build method to be implemented by each child class.

        :return: the built object
        """
        pass

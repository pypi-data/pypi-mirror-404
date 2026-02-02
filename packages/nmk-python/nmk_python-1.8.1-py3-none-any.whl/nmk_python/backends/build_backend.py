"""
Python build backend definition module
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import cast

from nmk._internal.envbackend_legacy import EnvBackend  # For type hinting
from nmk.model.model import NmkModel


class PythonBuildBackend(ABC):
    """
    Python build backend interface

    :param model: NmkModel instance
    """

    def __init__(self, model: NmkModel):
        self._model = model
        self._env_backend = cast(EnvBackend, model.env_backend)  # type: ignore

    @abstractmethod
    def install_editable(self):  # pragma: no cover
        """
        Install current project as editable package
        """
        pass

    @abstractmethod
    def install_wheel(self, wheel_path: Path):  # pragma: no cover
        """
        Install current project built wheel
        """
        pass

    @abstractmethod
    def build_wheel(self, build_dir: Path, built_wheel_name: str, wheel_version: str) -> Path:  # pragma: no cover
        """
        Build current project wheel

        :param build_dir: temporary build folder
        :param built_wheel_name: name of the built wheel file
        :return: path to built wheel
        """
        pass

    @abstractmethod
    def uninstall_wheels(self, wheel_names: list[str]):  # pragma: no cover
        """
        Uninstall specified wheels

        :param wheel_names: names of the wheels to uninstall
        """
        pass

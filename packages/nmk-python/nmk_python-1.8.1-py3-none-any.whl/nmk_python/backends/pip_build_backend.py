"""
Pip build backend module.
"""

import sys
from pathlib import Path
from typing import cast

from nmk.utils import run_with_logs

from .build_backend import PythonBuildBackend


class PipBuildBackend(PythonBuildBackend):
    """
    Pip build backend implementation

    :param model: NmkModel instance
    """

    def install_editable(self):
        # Prepare install args
        install_args = ["install", "-e", "."]

        # Add extra args from model config
        install_args += cast(list[str], self._model.config["pythonEditablePipInstallArgs"].value)

        # Delegate to subprocess
        self._env_backend.subprocess(install_args, cwd=self._env_backend.project_path)

    def install_wheel(self, wheel_path: Path):
        # Prepare install args
        install_args = ["install", str(wheel_path)]

        # Add extra args from model config
        install_args += cast(list[str], self._model.config["pythonWheelPipInstallArgs"].value)

        # Delegate to subprocess
        self._env_backend.subprocess(install_args, cwd=self._env_backend.project_path)

    def build_wheel(self, build_dir: Path, built_wheel_name: str, wheel_version: str) -> Path:
        # Delegate to build module
        run_with_logs([sys.executable, "-m", "build", "--wheel", "--skip-dependency-check", "--no-isolation"], cwd=build_dir)

        # Return built wheel path
        return build_dir / "dist" / built_wheel_name

    def uninstall_wheels(self, wheel_names: list[str]):
        # Prepare uninstall args
        uninstall_args = ["uninstall", "--yes"] + wheel_names

        # Delegate to subprocess
        self._env_backend.subprocess(uninstall_args, cwd=self._env_backend.project_path)

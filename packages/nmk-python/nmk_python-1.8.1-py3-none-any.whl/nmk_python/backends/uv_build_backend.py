"""
Uv build backend module.
"""

from pathlib import Path
from typing import cast

from .build_backend import PythonBuildBackend


class UvBuildBackend(PythonBuildBackend):
    """
    Uv build backend implementation

    :param model: NmkModel instance
    """

    def install_editable(self):
        # Prepare install args
        install_args = ["sync"]

        # Add extra args from model config
        install_args += cast(list[str], self._model.config["pythonEditableUvInstallArgs"].value)

        # Delegate to subprocess
        self._env_backend.subprocess(install_args, cwd=self._env_backend.project_path)

    def install_wheel(self, wheel_path: Path):
        # Prepare install args
        install_args = ["pip", "install", str(wheel_path)]

        # Add extra args from model config
        install_args += cast(list[str], self._model.config["pythonWheelUvInstallArgs"].value)

        # Delegate to subprocess
        self._env_backend.subprocess(install_args, cwd=self._env_backend.project_path)

    def build_wheel(self, build_dir: Path, built_wheel_name: str, wheel_version: str) -> Path:
        # Name for wheel sub-directory
        wheel_sub_dir = "wheel_dist"

        # Check for (experimental) uv-build backend
        if self._model.config["pythonUseUvBuildBackend"].value:
            # Prepare project version (without updating the venv)
            self._env_backend.subprocess(["version", "--active", "--no-sync", wheel_version], cwd=build_dir)

        # Delegate to uv
        build_args = ["build", "--wheel", "--out-dir", wheel_sub_dir]
        self._env_backend.subprocess(build_args, cwd=build_dir)

        # Return built wheel path
        return build_dir / wheel_sub_dir / built_wheel_name

    def uninstall_wheels(self, wheel_names: list[str]):
        # Same as setup
        self._env_backend.upgrade(full=False, only_deps=True)

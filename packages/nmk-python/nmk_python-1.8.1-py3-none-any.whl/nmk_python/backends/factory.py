"""
Build backend factory definition module
"""

from nmk.model.model import NmkModel

from .build_backend import PythonBuildBackend
from .pip_build_backend import PipBuildBackend
from .uv_build_backend import UvBuildBackend

# Supported backends mapping
_SUPPORTED_BACKENDS = {"pip": PipBuildBackend, "legacy": PipBuildBackend, "uv": UvBuildBackend}


class BuildBackendFactory:
    """
    Python build backend factory
    """

    @staticmethod
    def create(model: NmkModel) -> PythonBuildBackend:
        """
        Create a python build backend, from provided environment backend

        :param model: NmkModel instance
        :return: Python build backend instance
        """

        # Check for supported backend
        env_backend_name = model.env_backend.name
        assert env_backend_name in _SUPPORTED_BACKENDS, f"Unsupported backend for python build: {env_backend_name}"
        return _SUPPORTED_BACKENDS[env_backend_name](model)

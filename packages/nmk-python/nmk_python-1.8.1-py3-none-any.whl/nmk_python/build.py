"""
Python package build module
"""

import importlib.metadata
import json
import shutil
from fnmatch import fnmatch
from itertools import product
from pathlib import Path
from typing import cast

from nmk._internal.envbackend_legacy import EnvBackend  # For type hinting
from nmk.logs import NmkLogWrapper
from nmk.model.builder import NmkTaskBuilder
from nmk.model.model import NmkModel
from nmk.model.resolver import NmkDictConfigResolver, NmkListConfigResolver, NmkStrConfigResolver
from nmk.utils import is_windows
from packaging.requirements import Requirement

from nmk_python.backends.factory import BuildBackendFactory


# Install filter for Windows
def _can_install(name: str, logger: NmkLogWrapper) -> bool:
    # On Windows, refuse to install nmk package while running nmk (wont' work)
    if is_windows() and name in ["nmk", "buildenv"]:
        logger.warning(f"Can't install {name} while running {name}!")
        return False
    return True


# Get python package from model
def _python_package(model: NmkModel) -> str:
    cfg = model.config.get("pythonPackage")
    assert cfg is not None and isinstance(cfg.value, str), "Can't read pythonPackage from model"
    return cfg.value


class PackageBuilder(NmkTaskBuilder):
    """
    Python package builder
    """

    def build(self, project_file: str, version_file: str, source_dirs: list[str], artifacts_dir: str, build_dir: str, extra_resources: dict[str, str]):  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Delegate to python build module, from a temporary build folder

        :param project_file: path to python project file
        :param version_file: path to generated version file
        :param source_dirs: list of source folders for this wheel
        :param artifacts_dir: output folder for built wheel
        :param build_dir: temporary build folder
        :param extra_resources: dictionary of extra resources mapping (original path -> target path)
        """

        # Prepare build folder
        build_path = Path(build_dir)
        if build_path.is_dir():
            shutil.rmtree(build_path)
        build_path.mkdir(exist_ok=True, parents=True)

        # Copy source folders and various project files
        project_path = Path(project_file)
        project_root = project_path.parent
        for source_dir in map(Path, source_dirs):
            shutil.copytree(source_dir, build_path / source_dir.relative_to(project_root))
        for candidate in filter(lambda p: p.is_file(), map(Path, [project_path, version_file, project_root / "README.md", project_root / "LICENSE"])):
            dest = build_path / candidate.relative_to(project_root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(candidate, dest)

        # Handle extra resources
        for src, dst in extra_resources.items():
            src_path, dst_path = Path(src), Path(dst)
            if not src_path.is_absolute():  # pragma: no branch
                src_path = project_root / src_path
            if not dst_path.is_absolute():  # pragma: no branch
                dst_path = project_root / dst_path
            assert src_path.exists(), f"Required extra resource path not found: {src_path}"
            dst_path = build_path / dst_path.relative_to(project_root)
            dst_path.mkdir(exist_ok=True, parents=True)
            if src_path.is_file():
                # Single file copy
                self.logger.debug(f"Copy extra resource file: {src_path} --> {dst_path}")
                shutil.copyfile(src_path, dst_path / src_path.name)
            else:
                # Directory copy
                self.logger.debug(f"Copy extra resource tree: {src_path} --> {dst_path}")
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

        # Prepare artifacts folder
        artifacts_path = Path(artifacts_dir)
        artifacts_path.mkdir(exist_ok=True, parents=True)
        for wheel in artifacts_path.glob("*.whl"):
            wheel.unlink()

        # Read version from file
        wheel_version = Path(version_file).read_text().splitlines()[0]

        # Delegate to build backend
        built_wheel = BuildBackendFactory.create(self.model).build_wheel(
            build_dir=build_path, built_wheel_name=self.main_output.name, wheel_version=wheel_version
        )
        assert built_wheel.is_file(), f"Expected built wheel not found: {built_wheel}"

        # Copy wheel to artifacts folder
        shutil.copyfile(built_wheel, self.main_output)


class PythonModuleResolver(NmkStrConfigResolver):
    """
    Python module name resolver
    """

    def get_value(self, name: str) -> str:
        """
        Return module name from package (i.e. wheel) name
        """
        return _python_package(self.model).replace("-", "_")


class Installer(NmkTaskBuilder):
    """
    Install built wheel in venv
    """

    def build(self, name: str, wheel: str, pip_args: list[str] | None = None, to_remove: str = ""):  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Install wheel in venv

        :param name: wheel name to be installed
        :param wheel: wheel path to be installed
        :param pip_args: pip command line arguments; deprecated, not used anymore
        :param to_remove: stamp file to be removed
        """

        # Check if wheel can be installed
        if _can_install(name, self.logger):
            # Delegate to build backend
            eb = cast(EnvBackend, self.model.env_backend)  # type: ignore
            old_packages = eb.installed_packages
            BuildBackendFactory.create(self.model).install_wheel(wheel_path=Path(wheel))
            eb.print_updates(old_packages)

            # Remove stamp file
            Path(to_remove).unlink(missing_ok=True)


class Uninstaller(NmkTaskBuilder):
    """
    Uninstall current project wheel from venv
    """

    def build(self, name: str, local_deps: list[str] | None = None):  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Uninstall wheel from venv

        Note that task won't fail if the wheel is not installed

        :param name: wheel name to be uninstalled
        :param local_deps: list of workspace local dependencies patterns, used to find additional wheels to uninstall
        """

        # Find local deps to uninstall, from provided packages
        wheel_names = set([name])
        eb = cast(EnvBackend, self.model.env_backend)  # type: ignore
        old_packages = eb.installed_packages
        for pattern, dep_name in product(local_deps if local_deps else [], old_packages.keys()):
            if fnmatch(dep_name, pattern):
                self.logger.debug(f"wheel name '{dep_name}' matches local dependency pattern '{pattern}', will be uninstalled")
                wheel_names.add(dep_name)

        # Delegate to build backend
        BuildBackendFactory.create(self.model).uninstall_wheels(wheel_names=sorted(list(wheel_names)))
        eb.print_updates(old_packages)


class EditableBuilder(NmkTaskBuilder):
    """
    Install python project in editable mode
    """

    def build(self, pip_args: list[str] | None = None):  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Install project in venv as editable package

        :param pip_args: pip command line arguments; deprecated, not used anymore
        """

        # Check if project can be installed in editable mode
        if _can_install(_python_package(self.model), self.logger):
            # Delegate to build backend
            eb = cast(EnvBackend, self.model.env_backend)  # type: ignore
            old_packages = eb.installed_packages
            BuildBackendFactory.create(self.model).install_editable()
            eb.print_updates(old_packages)

            # Touch stamp file
            self.main_output.touch()


class PythonOptionalDepsResolver(NmkListConfigResolver):
    """
    Python optional deps resolver
    """

    def get_value(self, name: str, groups: dict[str, list[str]]) -> list[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Turn dependency options deps dict into a merged list of dependencies
        """
        return sorted(list(set(dependency for deps in groups.values() for dependency in deps)))


class PythonDevDepsResolver(NmkListConfigResolver):
    """
    Python development deps resolver
    """

    def get_value(self, name: str, package_deps: list[str], all_deps: list[str]) -> list[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Return development dependencies (all deps minus package deps)
        """
        return sorted(list(set(all_deps) - set(package_deps)))


class PythonArchiveDepsResolver(NmkDictConfigResolver):
    """
    Python archive dependencies resolver
    """

    def get_value(self, name: str, archives: list[str]) -> dict[str, str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Return archive dependencies mapping (python package name -> wheel path)
        """

        # Iterate on existing archives paths
        out: dict[str, str] = {}
        for dep in filter(lambda p: p.is_file() and "-" in p.name, map(Path, archives)):
            # Extract package name from wheel file name
            dep_name = dep.name.split("-")[0].replace("_", "-")
            out[dep_name] = str(dep.resolve()).replace("\\", "\\\\")  # Escape backslashes for Windows paths
        return out


# Internal/external dependencies keys
_INTERNAL_DEPS_KEY = "internal"
_EXTERNAL_DEPS_KEY = "external"


class DepsMetadataBuilder(NmkTaskBuilder):
    """
    Generate python dependencies metadata file
    """

    def build(self, root_name: str, local_deps: list[str]):  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Generate python dependencies metadata file

        :param root_name: name of the root package
        :param local_deps: list of workspace local dependencies patterns
        """

        # Normalization implementation
        def normalize(name: str) -> str:
            return name.lower().replace("_", "-")

        # Prepare distributions map
        distributions = {normalize(d.name): d for d in importlib.metadata.distributions()}
        assert root_name in distributions, f"Root package '{root_name}' not found in installed distributions"
        output_data: dict[str, dict[str, str]] = {_INTERNAL_DEPS_KEY: {}, _EXTERNAL_DEPS_KEY: {}}

        # Visitor implementation
        def visit(name: str):
            # Already visited or unknown?
            if (name in output_data[_INTERNAL_DEPS_KEY]) or (name in output_data[_EXTERNAL_DEPS_KEY]) or (name not in distributions):
                return

            # Check for internal/external dependency
            if name != root_name:
                if any(fnmatch(name, pattern) for pattern in local_deps):
                    # Internal dependency
                    output_data[_INTERNAL_DEPS_KEY][name] = distributions[name].version
                else:
                    # External dependency
                    output_data[_EXTERNAL_DEPS_KEY][name] = distributions[name].version

            # Visit dependencies
            for dep in distributions[name].requires or []:
                # Get requirement
                req = Requirement(dep)

                # Check marker, if any
                if req.marker is not None and not req.marker.evaluate():
                    continue

                # Visit dependency if installed
                visit(normalize(req.name))

        # Visit from root
        visit(root_name)

        # Write output metadata file
        self.main_output.write_text(
            json.dumps(
                {
                    _EXTERNAL_DEPS_KEY: {k: output_data[_EXTERNAL_DEPS_KEY][k] for k in sorted(output_data[_EXTERNAL_DEPS_KEY])},
                    _INTERNAL_DEPS_KEY: {k: output_data[_INTERNAL_DEPS_KEY][k] for k in sorted(output_data[_INTERNAL_DEPS_KEY])},
                },
                indent=4,
            )
        )

"""
Python files resolvers
"""

from abc import abstractmethod
from pathlib import Path
from typing import cast

from nmk.model.resolver import NmkListConfigResolver


class FilesFinder(NmkListConfigResolver):
    """
    Shared logic for files resolution
    """

    @abstractmethod
    def find_in_folders(self) -> list[str]:  # pragma: no cover
        """
        Folders to be browsed (to be overridden)

        :return: List of folders to be browsed for python files
        """
        pass

    def get_value(self, name: str) -> list[Path]:
        """
        Browse for source files in specified folders

        :param name: Config item name
        :return: List of found source files
        """
        # Iterate on source paths, and find all source files
        return [src_file for src_path in map(Path, self.find_in_folders()) for src_file in filter(lambda f: f.is_file(), src_path.rglob("*"))]


class PythonFilesFinder(FilesFinder):
    """Regular python files resolver"""

    def find_in_folders(self) -> list[str]:
        """
        Python source folders
        """
        return cast(list[str], self.model.config["pythonSrcFolders"].value)

    def get_value(self, name: str) -> list[Path]:
        """
        Browse for python files in specified folders

        Also and make sure they don't overlap with generated and test source code
        """
        # All found files
        all_files = set(super().get_value(name))

        # Remove generated and test ones
        all_files -= {Path(p) for p in cast(list[str], self.model.config["pythonTestSrcFiles"].value)}
        all_files -= {Path(p) for p in cast(list[str], self.model.config["pythonGeneratedSrcFiles"].value)}

        return list(all_files)


class PythonTestFilesFinder(FilesFinder):
    """Test python files resolver"""

    def find_in_folders(self) -> list[str]:
        """
        Python tests source folders
        """
        return [cast(str, self.model.config["pythonTestSources"].value)]

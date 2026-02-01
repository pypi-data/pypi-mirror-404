"""Base archiver class for extraction tools."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseArchiver(ABC):
    """Base class for archiver/extractor tools."""

    @abstractmethod
    def __init__(self, executable_path: str | Path) -> None:
        """Initialize the archiver.

        Args:
            executable_path: Path to the executable.
        """

    @property
    def archiver_name(self) -> str:
        """Get the archiver name."""
        return self.archiver_name

    @property
    def executable_name(self) -> str:
        """Get the executable name."""
        return self.executable_name

    @property
    def file_extensions(self) -> list[str]:
        """A non-abstract method that accesses the class impl for the file extensions."""
        return self.file_extensions

    @property
    def mime_types(self) -> list[str]:
        """A non-abstract method that accesses the class impl for the mime types."""
        return self.mime_types

    @abstractmethod
    def extract_archive(self, archive_path: Path, extract_dir: Path) -> None:
        """Extracts an archive to a specified directory.

        Args:
            archive_path (Path): The path to the archive file.
            extract_dir (Path): The directory to extract the archive to.

        """

    @abstractmethod
    def get_archive_uncompressed_size(self, archive_path: Path) -> int:
        """Get the uncompressed size of the contents.

        Args:
            archive_path (Path): The path to the archive file.

        """

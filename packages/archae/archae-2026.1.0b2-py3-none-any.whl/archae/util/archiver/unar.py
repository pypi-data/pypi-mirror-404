"""unar archiver/extractor implementation."""

import subprocess
from pathlib import Path
from typing import ClassVar

from .base_archiver import BaseArchiver


class UnarArchiver(BaseArchiver):
    """Archiver implementation for unar."""

    file_extensions: ClassVar[list[str]] = [
        "appinstaller",
        "appx",
        "appxbundle",
        "gz",
        "tgz",
        "emsix",
        "emsixbundle",
        "msix",
        "msixbundle",
        "apk",
        "deb",
        "cab",
        "pptx",
        "pptm ",
        "xlsx ",
        "xlsm",
        "docx",
        "docm",
        "7z",
        "s7z",
        "ace",
        "alz",
        "arc",
        "pak",
        "a",
        "ar",
        "deb",
        "lib",
        "arj",
        "bz2",
        "tbz2",
        "crx",
        "z",
        "taz",
        "cpio",
        "arc",
        "pak",
        "iso",
        "img",
        "lha",
        "lhz",
        "lzma",
        "msi",
        "msp",
        "rar",
        "r00",
        "sit",
        "sitx",
        "tar",
        "xar",
        "pkg",
        "xpi",
        "xz",
        "txz",
        "zoo",
        "zip",
        "zipx",
        "aar",
        "nsi",
        "exe",
        "nsis",
        "udf",
        "edb",
        "edp",
        "edr",
    ]
    mime_types: ClassVar[list[str]] = [
        "application/appinstaller",
        "application/appx",
        "application/appxbundle",
        "application/gzip",
        "application/msix",
        "application/msixbundle",
        "application/vnd.android.package-archive",
        "application/vnd.debian.binary-package",
        "application/vnd.ms-cab-compressed",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/x-7z-compressed",
        "application/x-ace-compressed",
        "application/x-alz-compressed",
        "application/x-arc",
        "application/x-archive",
        "application/x-arj",
        "application/x-bzip2",
        "application/x-chrome-extension",
        "application/x-compress",
        "application/x-cpio",
        "application/x-freearc",
        "application/x-iso9660-image",
        "application/x-lzh",
        "application/x-lzma",
        "application/x-ole-storage",
        "application/x-rar-compressed",
        "application/x-stuffit",
        "application/x-sit",
        "application/x-stuffitx",
        "application/x-sitx",
        "application/x-tar",
        "application/x-xar",
        "application/x-xpinstall",
        "application/x-xz",
        "application/x-zoo",
        "application/zip",
        "application/zip",
        "text/x-nsis",
    ]
    archiver_name: str = "unar"
    executable_name: str = "unar"

    def __init__(self, executable_path: str | Path) -> None:
        """Initialize the unar archiver.

        Args:
            executable_path: Path to the unar executable.
        """
        self.executable_path = Path(executable_path)

    def extract_archive(self, archive_path: Path, extract_dir: Path) -> None:
        """Extracts an archive to a specified directory.

        Args:
            archive_path (Path): The path to the archive file.
            extract_dir (Path): The directory to extract the archive to.

        """
        command: list[str] = [
            str(self.executable_path),
            "-o",
            str(extract_dir),
            str(archive_path),
        ]
        subprocess.run(command, check=True)  # noqa: S603

    def get_archive_uncompressed_size(self, archive_path: Path) -> int:  # noqa: ARG002
        """Get the uncompressed size of the contents.

        Args:
            archive_path (Path): The path to the archive file.

        Returns:
            int: The size of the contents
        """
        return -1

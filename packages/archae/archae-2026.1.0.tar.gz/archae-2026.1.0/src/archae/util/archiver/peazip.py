"""peazip archiver/extractor implementation."""

import subprocess
from pathlib import Path
from typing import ClassVar

from .base_archiver import BaseArchiver


class PeazipArchiver(BaseArchiver):
    """Archiver implementation for peazip."""

    file_extensions: ClassVar[list[str]] = [
        "appinstaller",
        "appx",
        "appxbundle",
        "gz",
        "tgz",
        "jar",
        "ear",
        "war",
        "emsix",
        "emsixbundle",
        "msix",
        "msixbundle",
        "apk",
        "deb",
        "cab",
        "chm",
        "chw",
        "chi",
        "chq",
        "pptx",
        "pptm ",
        "xlsx",
        "xlsm",
        "docx",
        "docm",
        "7z",
        "s7z",
        "ace",
        "dmg",
        "img",
        "arc",
        "pak",
        "arj",
        "br",
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
        "lzma",
        "wim",
        "swm",
        "esd",
        "msi",
        "msp",
        "rar",
        "r00",
        "rpm",
        "tar",
        "vhd",
        "vhdx",
        "xar",
        "pkg",
        "xpi",
        "xz",
        "txz",
        "ipa",
        "zip",
        "zipx",
        "aar",
        "zst",
    ]
    mime_types: ClassVar[list[str]] = [
        "application/appinstaller",
        "application/appx",
        "application/appxbundle",
        "application/gzip",
        "application/java-archive",
        "application/msix",
        "application/msixbundle",
        "application/vnd.android.package-archive",
        "application/vnd.debian.binary-package",
        "application/vnd.ms-cab-compressed",
        "application/vnd.ms-htmlhelp",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/x-7z-compressed",
        "application/x-ace-compressed",
        "application/x-apple-diskimage",
        "application/x-arc",
        "application/x-arj",
        "application/x-brotli",
        "application/x-bzip2",
        "application/x-chrome-extension",
        "application/x-compress",
        "application/x-cpio",
        "application/x-freearc",
        "application/x-iso9660-image",
        "application/x-lzma",
        "application/x-ms-wim",
        "application/x-ole-storage",
        "application/x-rar-compressed",
        "application/x-rpm",
        "application/x-tar",
        "application/x-vhd",
        "application/x-xar",
        "application/x-xpinstall",
        "application/x-xz",
        "application/zip",
        "application/zip",
        "application/zip",
        "application/zstd",
    ]
    archiver_name: str = "peazip"
    executable_name: str = "pea"

    def __init__(self, executable_path: str | Path) -> None:
        """Initialize the peazip archiver.

        Args:
            executable_path: Path to the peazip executable.
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
            "-ext2simple",
            str(archive_path),
            str(extract_dir),
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

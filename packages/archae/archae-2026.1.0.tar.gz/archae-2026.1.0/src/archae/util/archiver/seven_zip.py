"""7zip archiver/extractor implementation."""

import subprocess
from pathlib import Path
from typing import ClassVar

from .base_archiver import BaseArchiver


class SevenZipArchiver(BaseArchiver):
    """Archiver implementation for 7zip."""

    file_extensions: ClassVar[list[str]] = [
        "7z",
        "s7z",
        "apk",
        "bz2",
        "tbz2",
        "crx",
        "xpi",
        "deb",
        "gz",
        "tgz",
        "ipa",
        "jar",
        "ear",
        "war",
        "lzma",
        "cab",
        "docx",
        "docm",
        "pptx",
        "pptm",
        "xlsx",
        "xlsm",
        "emsix",
        "emsixbundle",
        "msix",
        "appinstaller",
        "appx",
        "appxbundle",
        "msixbundle",
        "z",
        "taz",
        "tar",
        "zip",
        "zipx",
        "appimage",
        "dmg ",
        "img",
        "arj",
        "cpio",
        "cramfs",
        "raw",
        "alz",
        "ext",
        "ext2",
        "ext3",
        "ext4",
        "xar",
        "pkg",
        "fat",
        "gpt",
        "hfs",
        "hfsx",
        "iso",
        "lha",
        "lhz",
        "mbr",
        "chm",
        "chw",
        "chi",
        "chq",
        "msi",
        "msp",
        "vhd",
        "vhdx",
        "ntfs",
        "nsi",
        "exe",
        "nsis",
        "qcow2",
        "qcow",
        "qcow2c",
        "rpm",
        "rar",
        "r00",
        "sqfs",
        "sfs",
        "sqsh",
        "squashfs",
        "scap",
        "uefif",
        "udf",
        "edb",
        "edp",
        "edr",
        "a",
        "ar",
        "deb",
        "lib",
        "vdi",
        "vmdk",
        "wim",
        "swm",
        "esd",
        "xz",
        "txz",
    ]
    mime_types: ClassVar[list[str]] = [
        "application/x-7z-compressed",
        "application/vnd.android.package-archive",
        "application/x-bzip2",
        "application/x-chrome-extension",
        "application/x-xpinstall",
        "application/vnd.debian.binary-package",
        "application/gzip",
        "application/java-archive",
        "application/x-lzma",
        "application/vnd.ms-cab-compressed",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/msix",
        "application/appinstaller",
        "application/appx",
        "application/appxbundle",
        "application/msixbundle",
        "application/x-compress",
        "application/x-tar",
        "application/zip",
        "application/x-apple-diskimage",
        "application/x-arj",
        "application/x-cpio",
        "application/vnd.efi.img",
        "application/x-alz-compressed",
        "application/x-xar",
        "application/x-iso9660-image",
        "application/x-lzh",
        "application/vnd.ms-htmlhelp",
        "application/x-ole-storage",
        "application/x-vhd",
        "text/x-nsis",
        "application/x-qemu-disk",
        "application/x-rpm",
        "application/x-rar-compressed",
        "application/vnd.squashfs",
        "application/x-archive",
        "application/x-virtualbox-vdi",
        "application/x-vmdk-disk",
        "application/x-ms-wim",
        "application/x-xz",
    ]
    archiver_name: str = "7zip"
    executable_name: str = "7z"

    def __init__(self, executable_path: str | Path) -> None:
        """Initialize the 7zip archiver.

        Args:
            executable_path: Path to the 7zip executable.
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
            "x",
            str(archive_path),
            f"-o{extract_dir!s}",
        ]
        subprocess.run(command, check=True)  # noqa: S603

    def get_archive_uncompressed_size(self, archive_path: Path) -> int:
        """Get the uncompressed size of the contents.

        Args:
            archive_path (Path): The path to the archive file.

        Returns:
            int: The size of the contents
        """
        command: list[str] = [str(self.executable_path), "l", "-slt", str(archive_path)]
        result = subprocess.run(command, check=True, capture_output=True, text=True)  # noqa: S603

        result_lines = str(result.stdout).splitlines()
        exploded_size = 0
        for line in result_lines:
            if line.startswith("Size = "):
                exploded_size += int(line[7:])

        return exploded_size

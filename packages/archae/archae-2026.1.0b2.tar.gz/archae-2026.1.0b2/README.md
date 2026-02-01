<!-- start docs-include-index -->

# Archae

![Archae Logo of a spider exploring a sarcophagus](./_static/archae_logo.png)

[![PyPI](https://img.shields.io/pypi/v/archae)](https://img.shields.io/pypi/v/archae)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/archae)](https://pypi.org/project/archae/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/shawngmc/archae/main.svg)](https://results.pre-commit.ci/latest/github/shawngmc/archae/main)
[![Test](https://github.com/shawngmc/archae/actions/workflows/test.yml/badge.svg)](https://github.com/shawngmc/archae/actions/workflows/test.yml)
[![Documentation Status](https://readthedocs.org/projects/archae/badge/?version=latest)](https://archae.readthedocs.io/en/latest/?badge=latest)
[![PyPI - License](https://img.shields.io/pypi/l/archae)](https://img.shields.io/pypi/l/archae)

Archae explodes archives.

<!-- end docs-include-index -->

## Why

Every once and a while, I run into an issue: multiple layers of archives. The reasons vary, but examples would include:

- Searching for something in a ZIP of folders that contained a ZIP with a CD image in it
- Running a malware scan and finding an obscure archive format was missed and not even flagged
  Meanwhile, I want to make sure I don't fill my disk, especially if an archive bomb (more commonly known as a ZIP bomb) has been jammed in somewhere. They're only funny the first time. :D

## Features

- Uses 7z/peazip/unar (not 7za/7zr) to try to extract archives
- No substantial limit on the number of archive layers
- Identifies file types via libmagic
- Detects duplicate archives
- Basic archive bomb protections
    - min_archive_size_bytes - ensures the uncompressed size of an archive is limited
    - min_total_size_bytes - ensures the total extracted footprint isn't above a certain size
    - min_archive_ratio - ensures very-high-compression-ratio archives are stopped

## Installation

<!-- start docs-include-installation -->

Archae is available on [PyPI](https://pypi.org/project/archae/). Install with [uv](https://docs.astral.sh/uv/) or your package manager of choice:

```sh
uv tool install archae
```

<!-- end docs-include-installation -->

## Documentation

Check out the [Archae documentation](https://archae.readthedocs.io/en/stable/) for the [User's Guide](https://archae.readthedocs.io/en/stable/usage.html) and [CLI Reference](https://archae.readthedocs.io/en/stable/cli.html).

## Usage

<!-- start docs-include-usage -->

Running `archae --help` or `python -m archae --help` shows a list of all of the available options and arguments:

<!-- [[[cog
import cog
from archae import cli
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(cli.cli, ["--help"], terminal_width=88)
help = result.output.replace("Usage: cli", "Usage: archae")
cog.outl(f"\n```sh\narchae --help\n{help.rstrip()}\n```\n")
]]] -->

```sh
archae --help

 Usage: archae [OPTIONS] ARCHIVE_PATH

 Archae explodes archives.

╭─ Arguments ──────────────────────────────────────────────────────────────────────────╮
│ *  ARCHIVE_PATH  FILE  Archive to examine [required]                                 │
╰──────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────╮
│ --max_total_size_bytes        FILESIZE               Maximum total extraction size   │
│                                                      before failing, default 100G    │
│                                                      [default: 107374182400]         │
│ --max_archive_size_bytes      FILESIZE               Maximum individual archive      │
│                                                      extraction size before failing, │
│                                                      default 10G [default:           │
│                                                      10737418240]                    │
│ --min_archive_ratio           FLOAT RANGE [0<=x<=1]  Minimum allowed compression     │
│                                                      ratio for an archive. A         │
│                                                      floating-point value between    │
│                                                      0.0 and 1.0, inclusive. Default │
│                                                      is 0.005 [default: 0.005]       │
│ --version                 -v                         Show the version and exit.      │
│ --help                    -h                         Show this message and exit.     │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```

<!-- [[[end]]] -->

<!-- end docs-include-usage -->

## TODOs

- More archive bomb protections
    - min_total_size_bytes - (NYI) ensures the total extracted footprint isn't above a certain size
    - min_free_space - minimum free space at the extraction location
    - delete_archives_as_exploded - remove archive files to reduce duplication (boolean)
    - max_archive_depth - allow setting a maximum archive depth
- Improve archive type detection
- Separate between extractable and non-extractable archive types
- Detect password-protected archives
- Allow supplying archive passwords by hash
- Add custom magic to detect obscure archive formats

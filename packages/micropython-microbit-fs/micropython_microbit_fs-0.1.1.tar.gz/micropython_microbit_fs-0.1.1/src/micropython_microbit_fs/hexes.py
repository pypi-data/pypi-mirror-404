"""
Bundled MicroPython hex files for micro:bit.

This module provides access to the bundled MicroPython Intel Hex files
for micro:bit V1 and V2. The hex files are organised in the `hexes/` directory
using the following folder structure:

    hexes/
        microbitv1/
            v{semver}/
                filename-v{semver}.hex
        microbitv2/
            v{semver}/
                filename-v{semver}.hex

The micro:bit version and MicroPython version are determined by the folder path,
not the filename.

Example paths:
    - hexes/microbitv1/v1.1.1/micropython-microbit-v1.1.1.hex
    - hexes/microbitv2/v2.1.2/micropython-microbit-v2.1.2.hex
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Optional

from packaging.version import Version

from micropython_microbit_fs.exceptions import HexNotFoundError

# Regex patterns for device/version folders
DEVICE_FOLDER_PATTERN = re.compile(r"^microbitv(\d+)$")
VERSION_FOLDER_PATTERN = re.compile(r"^v(\d+\.\d+\.\d+)$")


@dataclass(frozen=True)
class MicroPythonHex:
    """Metadata and contents for a bundled MicroPython hex file."""

    file_path: Path
    version: str
    device_version: int
    content: str


def _get_hexes_dir() -> Path:
    """Get the path to the bundled hexes directory."""
    # Use importlib.resources to access package data
    return Path(str(resources.files("micropython_microbit_fs") / "hexes"))


def list_bundled_versions(device_version: Optional[int] = None) -> dict[int, list[str]]:
    """List available MicroPython versions.

    Example::
        >>> list_bundled_versions()
        {1: ['1.1.1'], 2: ['2.1.2']}
        >>> list_bundled_versions(1)
        {1: ['1.1.1']}

    :param device_version: The micro:bit device version (1 or 2). ``None`` lists all.
    :return: Mapping of device version to sorted versions (newest first).
    """
    hexes_dir = _get_hexes_dir()

    # Determine which device folders to inspect
    target_devices: list[int]
    if device_version is None:
        target_devices = []
        for entry in hexes_dir.iterdir():
            if not entry.is_dir():
                continue
            match = DEVICE_FOLDER_PATTERN.match(entry.name)
            if match:
                target_devices.append(int(match.group(1)))
    else:
        target_devices = [device_version]

    versions_by_device: dict[int, list[str]] = {}

    for target in target_devices:
        device_dir = hexes_dir / f"microbitv{target}"
        versions: list[str] = []

        if device_dir.exists():
            for version_folder in device_dir.iterdir():
                if not version_folder.is_dir():
                    continue
                match = VERSION_FOLDER_PATTERN.match(version_folder.name)
                if match:
                    semver = match.group(1)
                    # Hex filename is not important, but ensure exactly one exists
                    hex_files = [
                        p
                        for p in version_folder.iterdir()
                        if p.suffix.lower() == ".hex"
                    ]
                    if len(hex_files) != 1:
                        raise HexNotFoundError(
                            f"Unexpected number of hex files found in path {version_folder} (should be exactly 1)."
                        )
                    versions.append(semver)

        versions.sort(key=lambda v: Version(v), reverse=True)
        versions_by_device[target] = versions

    return versions_by_device


def get_bundled_hex(
    device_version: int, version: Optional[str] = None
) -> MicroPythonHex:
    """Get a bundled MicroPython hex file and metadata.

    :param device_version: The micro:bit device version (1 or 2).
    :param version: Optional MicroPython version string (e.g., "1.1.0").
        If not provided, returns the latest available version.
    :return: A frozen dataclass with filename, version string, and file contents.
    :raises HexNotFoundError: If no hex file is found for the specified
        device/version.

    Example::

        >>> hex_file = get_bundled_hex(1)  # Get latest V1 hex
        >>> hex_file.file_path.name
        'micropython-microbit-v1.1.1.hex'
        >>> hex_file.version
        '1.1.1'
        >>> hex_file.device_version
        1
        >>> hex_file.content[:2]
        '::'
    """
    available_versions_map = list_bundled_versions(device_version)
    available_versions = available_versions_map.get(device_version, [])
    if not available_versions:
        raise HexNotFoundError(
            f"No bundled MicroPython hex files found for micro:bit V{device_version}."
        )

    if version is None:
        # Use the latest version (first in the sorted list)
        selected_version = available_versions[0]
    else:
        if version not in available_versions:
            raise HexNotFoundError(
                f"MicroPython version '{version}' not found for micro:bit V{device_version}. "
                f"Available versions: {', '.join(available_versions)}"
            )
        selected_version = version

    # list_bundled_versions() ensures a single hex file exists in the version folder
    hex_path = _get_hexes_dir() / f"microbitv{device_version}" / f"v{selected_version}"
    hex_files = [p for p in hex_path.iterdir() if p.suffix.lower() == ".hex"]
    hex_file = hex_files[0]
    return MicroPythonHex(
        file_path=hex_file,
        version=selected_version,
        device_version=device_version,
        content=hex_file.read_text(),
    )

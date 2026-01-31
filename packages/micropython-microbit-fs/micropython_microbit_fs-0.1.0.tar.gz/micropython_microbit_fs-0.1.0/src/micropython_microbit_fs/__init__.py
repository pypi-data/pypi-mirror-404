#!/usr/bin/env python3
"""
micropython-microbit-fs: Inject and extract files from MicroPython Intel Hex files.

This library provides a simple API for working with MicroPython filesystem
embedded in Intel Hex files for the BBC micro:bit.

Main functions:
    - add_files: Add files to a MicroPython hex file
    - get_files: Read files from a MicroPython hex file
    - get_device_info: Get device memory information from a hex file
    - get_bundled_hex: Get a bundled MicroPython hex file
    - list_bundled_versions: List available bundled hex versions
"""

from micropython_microbit_fs.api import (
    add_files,
    get_device_info,
    get_files,
)
from micropython_microbit_fs.device_info import DeviceInfo, DeviceVersion
from micropython_microbit_fs.exceptions import (
    FilesystemError,
    HexNotFoundError,
    InvalidFileError,
    InvalidHexError,
    NotMicroPythonError,
    StorageFullError,
)
from micropython_microbit_fs.file import File
from micropython_microbit_fs.hexes import (
    MicroPythonHex,
    get_bundled_hex,
    list_bundled_versions,
)

__version__ = "0.1.0"

__all__ = [
    # Main API functions
    "add_files",
    "get_files",
    "get_device_info",
    # Bundled hex functions
    "MicroPythonHex",
    "get_bundled_hex",
    "list_bundled_versions",
    # Data classes
    "File",
    "DeviceInfo",
    "DeviceVersion",
    # Exceptions
    "FilesystemError",
    "InvalidHexError",
    "NotMicroPythonError",
    "InvalidFileError",
    "StorageFullError",
    "HexNotFoundError",
]

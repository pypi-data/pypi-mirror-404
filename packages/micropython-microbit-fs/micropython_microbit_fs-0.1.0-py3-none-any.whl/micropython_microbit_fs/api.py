#!/usr/bin/env python3
"""
Main public API for micropython-microbit-fs.

This module provides the main functions for working with micro:bit MicroPython
filesystems in Intel Hex files.
"""

from micropython_microbit_fs.device_info import DeviceInfo, get_device_info_ih
from micropython_microbit_fs.exceptions import InvalidFileError, InvalidHexError
from micropython_microbit_fs.file import File
from micropython_microbit_fs.filesystem import (
    add_files_to_hex,
    read_files_from_hex,
)
from micropython_microbit_fs.hex_utils import hex_to_string, load_hex


def add_files(
    hex_data: str,
    files: list[File],
) -> str:
    """
    Add files to a micro:bit MicroPython Intel Hex file.

    Takes a micro:bit MicroPython hex file and a list of files to add,
    returning a new hex file with the files encoded in the filesystem region.

    :param hex_data: Intel Hex file content as a string.
    :param files: List of File objects to inject into the filesystem.
    :returns: New Intel Hex file content with the files injected.

    :raises InvalidHexError: If the hex data is invalid.
    :raises NotMicroPythonError: If the hex does not contain MicroPython.
    :raises InvalidFileError: If a file has invalid name or content.
    :raises StorageFullError: If the files don't fit in the filesystem.

    Example::

        >>> import micropython_microbit_fs as micropython
        >>> files = [micropython.File.from_text("main.py", "print('Hello!')")]
        >>> new_hex = micropython.add_files(micropython_hex, files)
    """
    try:
        ih = load_hex(hex_data)
    except Exception as e:
        raise InvalidHexError(f"Failed to parse Intel Hex data: {e}") from e
    device_info = get_device_info_ih(ih)

    files_dict = {}
    for file in files:
        if file.name in files_dict:
            raise InvalidFileError(f"Duplicate file name: {file.name}")
        files_dict[file.name] = file.content
    add_files_to_hex(ih, device_info, files_dict)

    return hex_to_string(ih)


def get_files(hex_data: str) -> list[File]:
    """
    Get files from a micro:bit MicroPython Intel Hex file.

    Reads a micro:bit MicroPython hex file and returns all files found in the
    filesystem region.

    :param hex_data: Intel Hex file content as a string.
    :returns: List of File objects found in the filesystem.

    :raises InvalidHexError: If the hex data is invalid.
    :raises NotMicroPythonError: If the hex does not contain MicroPython.
    :raises FilesystemError: If the filesystem structure is corrupted.

    Example::

        >>> import micropython_microbit_fs as micropython
        >>> files = micropython.get_files(hex_with_files)
        >>> for f in files:
        ...     print(f"{f.name}: {f.size} bytes")
    """
    try:
        ih = load_hex(hex_data)
    except Exception as e:
        raise InvalidHexError(f"Failed to parse Intel Hex data: {e}") from e
    device_info = get_device_info_ih(ih)
    files_dict = read_files_from_hex(ih, device_info)
    return [File(name=name, content=content) for name, content in files_dict.items()]


def get_device_info(hex_data: str) -> DeviceInfo:
    """
    Get device memory information from a MicroPython Intel Hex file.

    Extracts information about the flash memory layout, including
    filesystem boundaries and MicroPython version.

    :param hex_data: Intel Hex file content as a string.
    :returns: DeviceInfo containing memory layout information.

    :raises InvalidHexError: If the hex data is invalid.
    :raises NotMicroPythonError: If the hex does not contain MicroPython.

    Example::

        >>> import micropython_microbit_fs as micropython
        >>> info = micropython.get_device_info(micropython_hex)
        >>> print(f"FS Size: {info.fs_size} bytes")
        >>> print(f"MicroPython: {info.micropython_version}")
    """
    try:
        ih = load_hex(hex_data)
    except Exception as e:
        raise InvalidHexError(f"Failed to parse Intel Hex data: {e}") from e
    return get_device_info_ih(ih)

#!/usr/bin/env python3
"""Device memory information data structures."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DeviceVersion(Enum):
    """micro:bit hardware version."""

    V1 = "V1"  # micro:bit V1 (nRF51822)
    V2 = "V2"  # micro:bit V2 (nRF52833)


@dataclass(frozen=True)
class DeviceSpec:
    """Hardware specification for a micro:bit version."""

    device_version: DeviceVersion
    uicr_magic: int
    page_size: int
    flash_start_address: int
    flash_size: int
    fs_end_address: int


DEVICE_SPECS = {
    DeviceVersion.V1: DeviceSpec(
        device_version=DeviceVersion.V1,
        uicr_magic=0x17EEB07C,
        page_size=1024,
        flash_start_address=0,
        flash_size=256 * 1024,
        fs_end_address=256 * 1024,
    ),
    DeviceVersion.V2: DeviceSpec(
        device_version=DeviceVersion.V2,
        uicr_magic=0x47EEB07C,
        page_size=4096,
        flash_start_address=0,
        flash_size=512 * 1024,
        fs_end_address=0x73000,
    ),
}


@dataclass(frozen=True)
class DeviceInfo:
    """
    Device information extracted from a MicroPython hex file.

    This contains information about the flash memory layout including
    where the MicroPython runtime and filesystem are located.
    """

    flash_page_size: int
    """Size of a flash page in bytes (V1: 1024, V2: 4096)."""

    flash_size: int
    """Total flash size in bytes (V1: 256KB, V2: 512KB)."""

    flash_start_address: int
    """Start address of flash memory (always 0)."""

    flash_end_address: int
    """End address of flash memory."""

    runtime_start_address: int
    """Start address of the MicroPython runtime."""

    runtime_end_address: int
    """End address of the MicroPython runtime."""

    fs_start_address: int
    """Start address of the filesystem region."""

    fs_end_address: int
    """End address of the filesystem region."""

    micropython_version: str
    """MicroPython version string."""

    device_version: DeviceVersion
    """micro:bit hardware version (V1 or V2)."""

    @property
    def fs_size(self) -> int:
        """Total filesystem size in bytes."""
        # One page is used as scratch, so exclude it from the size
        return self.fs_end_address - self.fs_start_address - self.flash_page_size


def get_device_info_ih(ih: Any) -> DeviceInfo:
    """
    Internal function to get device info from an already-loaded IntelHex.

    :param ih: IntelHex object.
    :returns: DeviceInfo containing memory layout information.

    :raises NotMicroPythonError: If the hex does not contain MicroPython.
    """
    # Delayed imports to avoid circular dependency
    from micropython_microbit_fs.exceptions import NotMicroPythonError
    from micropython_microbit_fs.flash_regions import get_device_info_from_flash_regions
    from micropython_microbit_fs.uicr import get_device_info_from_uicr

    # First try Flash Regions Table detection, as it's more likely to be a V2
    device_info = get_device_info_from_flash_regions(ih)
    if device_info is not None:
        return device_info

    # Try UICR detection next (works for V1 and pre-release V2)
    device_info = get_device_info_from_uicr(ih)
    if device_info is not None:
        return device_info

    raise NotMicroPythonError(
        "Could not detect MicroPython in hex file. "
        "The hex file may not contain MicroPython or may be corrupted."
    )

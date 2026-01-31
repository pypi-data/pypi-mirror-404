#!/usr/bin/env python3
"""
Parse UICR data from micro:bit MicroPython hex files.

The UICR (User Information Configuration Registers) contains MicroPython
specific data including:
- Magic value to identify MicroPython
- Flash page size
- Runtime start/end pages
- Version string location

For more info:
https://microbit-micropython.readthedocs.io/en/latest/devguide/hexformat.html
"""

from __future__ import annotations

from intelhex import IntelHex

from micropython_microbit_fs.device_info import DEVICE_SPECS, DeviceInfo
from micropython_microbit_fs.hex_utils import (
    read_string,
    read_uint16,
    read_uint32,
)

# UICR addresses
UICR_START = 0x10001000
UICR_CUSTOMER_OFFSET = 0x80
UICR_CUSTOMER_UPY_OFFSET = 0x40
UICR_UPY_START = UICR_START + UICR_CUSTOMER_OFFSET + UICR_CUSTOMER_UPY_OFFSET

# UICR field addresses
UicrAddress = {
    "MAGIC": UICR_UPY_START + 0,  # 4 bytes - Magic value,
    "END_MARKER": UICR_UPY_START + 4,  # 4 bytes - End marker
    "PAGE_SIZE": UICR_UPY_START + 8,  # 4 bytes - Page size (log2)
    "START_PAGE": UICR_UPY_START + 12,  # 2 bytes - Start page number
    "PAGES_USED": UICR_UPY_START + 14,  # 2 bytes - Number of pages used
    "DELIMITER": UICR_UPY_START + 16,  # 4 bytes - Delimiter
    "VERSION_LOC": UICR_UPY_START + 20,  # 4 bytes - Address of version string
    "REG_TERMINATOR": UICR_UPY_START + 24,  # 4 bytes - Flash regions terminator
}


def get_device_info_from_uicr(ih: IntelHex) -> DeviceInfo | None:
    """
    Extract DeviceInfo from UICR data in an IntelHex object.

    :param ih: IntelHex object containing the hex data.
    :returns: DeviceInfo if valid MicroPython UICR data is found, None otherwise.
    """
    magic = read_uint32(ih, UicrAddress["MAGIC"])
    page_size_log2 = read_uint32(ih, UicrAddress["PAGE_SIZE"])
    start_page = read_uint16(ih, UicrAddress["START_PAGE"])
    pages_used = read_uint16(ih, UicrAddress["PAGES_USED"])
    version_address = read_uint32(ih, UicrAddress["VERSION_LOC"])

    for device in DEVICE_SPECS.values():
        if device.uicr_magic == magic:
            device_spec = device
            break
    else:
        # Unknown magic value
        return None

    page_size = 2**page_size_log2
    flash_size = device_spec.flash_size
    flash_start = start_page * page_size
    flash_end = flash_start + device_spec.flash_size
    runtime_start = flash_start
    runtime_end = pages_used * page_size
    fs_start = runtime_end
    fs_end = device_spec.fs_end_address
    version = read_string(ih, version_address)
    device_version = device_spec.device_version

    return DeviceInfo(
        flash_page_size=page_size,
        flash_size=flash_size,
        flash_start_address=flash_start,
        flash_end_address=flash_end,
        runtime_start_address=runtime_start,
        runtime_end_address=runtime_end,
        fs_start_address=fs_start,
        fs_end_address=fs_end,
        micropython_version=version,
        device_version=device_version,
    )

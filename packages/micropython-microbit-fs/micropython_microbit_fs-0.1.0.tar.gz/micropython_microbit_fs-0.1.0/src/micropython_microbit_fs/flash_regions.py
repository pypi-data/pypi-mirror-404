"""
Parse Flash Regions Table from MicroPython V2 hex files.

The micro:bit flash layout is divided in flash regions, each containing a
different type of data (Nordic SoftDevice, MicroPython, bootloader, etc).
One of the regions is dedicated to the micro:bit filesystem, and this info
is used by this library to add the user files into a MicroPython hex file.

The Flash Regions Table stores a data table at the end of the last flash page
used by the MicroPython runtime.

Table format (from end of page, reading backwards):
```
| MAGIC_1 (4) | VERSION (2) | TABLE_LEN (2) | REG_COUNT (2) | P_SIZE (2) | MAGIC_2 (4) |
| Row N: ID (1) | HT (1) | START_PAGE (2) | LENGTH (4) | HASH_DATA (8) |
| ...
| Row 1: ID (1) | HT (1) | START_PAGE (2) | LENGTH (4) | HASH_DATA (8) |
```

More information:
https://github.com/microbit-foundation/micropython-microbit-v2/blob/v2.0.0-beta.3/src/addlayouttable.py
"""

from __future__ import annotations

from dataclasses import dataclass

from intelhex import IntelHex

from micropython_microbit_fs import hex_utils as ihex
from micropython_microbit_fs.device_info import DEVICE_SPECS, DeviceInfo, DeviceVersion

FLASH_REGIONS_MAGIC_1 = 0x597F30FE
"""First magic value for flash regions table."""

FLASH_REGIONS_MAGIC_2 = 0xC1B1D79D
"""Second magic value for flash regions table."""

FLASH_REGIONS_HEADER_SIZE = 8
"""Size of flash regions table header (2 magic words)."""


class FlashRegionId:
    """Flash region identifiers."""

    SOFTDEVICE = 1
    """SoftDevice (Bluetooth stack) region."""

    MICROPYTHON = 2
    """MicroPython runtime region."""

    FILESYSTEM = 3
    """Filesystem region."""


# Header field sizes (bytes)
MAGIC_1_SIZE = 4
VERSION_SIZE = 2
TABLE_LEN_SIZE = 2
REG_COUNT_SIZE = 2
PAGE_SIZE_LOG2_SIZE = 2
MAGIC_2_SIZE = 4

# Header total size
HEADER_SIZE = (
    MAGIC_1_SIZE
    + VERSION_SIZE
    + TABLE_LEN_SIZE
    + REG_COUNT_SIZE
    + PAGE_SIZE_LOG2_SIZE
    + MAGIC_2_SIZE
)

# Header field offsets from end of page (reading backwards)
OFFSET_MAGIC_2 = MAGIC_2_SIZE
OFFSET_PAGE_SIZE_LOG2 = OFFSET_MAGIC_2 + PAGE_SIZE_LOG2_SIZE
OFFSET_REG_COUNT = OFFSET_PAGE_SIZE_LOG2 + REG_COUNT_SIZE
OFFSET_TABLE_LEN = OFFSET_REG_COUNT + TABLE_LEN_SIZE
OFFSET_VERSION = OFFSET_TABLE_LEN + VERSION_SIZE
OFFSET_MAGIC_1 = OFFSET_VERSION + MAGIC_1_SIZE

# Region row field sizes (bytes)
ROW_ID_SIZE = 1
ROW_HASH_TYPE_SIZE = 1
ROW_START_PAGE_SIZE = 2
ROW_LENGTH_SIZE = 4
ROW_HASH_DATA_SIZE = 8
ROW_SIZE = (
    ROW_ID_SIZE
    + ROW_HASH_TYPE_SIZE
    + ROW_START_PAGE_SIZE
    + ROW_LENGTH_SIZE
    + ROW_HASH_DATA_SIZE
)

# Region row field offsets from end of row (reading backwards)
ROW_OFFSET_HASH_DATA = ROW_HASH_DATA_SIZE
ROW_OFFSET_LENGTH = ROW_OFFSET_HASH_DATA + ROW_LENGTH_SIZE
ROW_OFFSET_START_PAGE = ROW_OFFSET_LENGTH + ROW_START_PAGE_SIZE
ROW_OFFSET_HASH_TYPE = ROW_OFFSET_START_PAGE + ROW_HASH_TYPE_SIZE
ROW_OFFSET_ID = ROW_OFFSET_HASH_TYPE + ROW_ID_SIZE


class RegionHashType:
    """Hash type field values in region rows."""

    EMPTY = 0
    """The hash data is empty."""

    DATA = 1
    """The full hash data field is used as a hash of the region in flash."""

    POINTER = 2
    """The 4 LSB bytes of the hash data field are used as a pointer."""


@dataclass
class RegionRow:
    """Data from a region row in the Flash Regions Table."""

    id: int
    start_page: int
    length_bytes: int
    hash_type: int
    hash_data: int
    hash_pointer_data: str


@dataclass
class TableHeader:
    """Flash Regions Table header data."""

    page_size_log2: int
    page_size: int
    region_count: int
    table_length: int
    version: int
    start_address: int
    end_address: int


def _find_table_header(ih: IntelHex, page_size: int) -> TableHeader | None:
    """
    Search for the Flash Regions Table header by scanning page boundaries.

    :param ih: IntelHex object containing the hex data.
    :param page_size: Flash page size to scan (default: 4096 for V2).
    :returns: TableHeader if found, None otherwise.
    """
    # Get the address range in the hex file
    min_addr = ih.minaddr()
    max_addr = ih.maxaddr()

    # Check if hex file is empty or has no valid data
    if min_addr is None or max_addr is None:
        return None

    # Scan pages from end to beginning, looking for magic values
    # Start from the first page boundary after min_addr
    start_page = (min_addr // page_size) * page_size
    end_page = ((max_addr // page_size) + 1) * page_size

    for page_start in range(start_page, end_page, page_size):
        page_end = page_start + page_size

        # Read magic values from end of page
        magic_1_addr = page_end - OFFSET_MAGIC_1
        magic_2_addr = page_end - OFFSET_MAGIC_2

        # Check if addresses are in range
        if magic_1_addr < min_addr or magic_2_addr + 4 > max_addr + 1:
            continue

        magic_1 = ihex.read_uint32(ih, magic_1_addr)
        magic_2 = ihex.read_uint32(ih, magic_2_addr)

        if magic_1 == FLASH_REGIONS_MAGIC_1 and magic_2 == FLASH_REGIONS_MAGIC_2:
            # Found the table header
            version = ihex.read_uint16(ih, page_end - OFFSET_VERSION)
            table_length = ihex.read_uint16(ih, page_end - OFFSET_TABLE_LEN)
            region_count = ihex.read_uint16(ih, page_end - OFFSET_REG_COUNT)
            page_size_log2 = ihex.read_uint16(ih, page_end - OFFSET_PAGE_SIZE_LOG2)

            return TableHeader(
                page_size_log2=page_size_log2,
                page_size=2**page_size_log2,
                region_count=region_count,
                table_length=table_length,
                version=version,
                start_address=page_end - OFFSET_MAGIC_1,
                end_address=page_end,
            )

    return None


def _read_region_row(ih: IntelHex, row_end_address: int) -> RegionRow:
    """
    Read a region row from the Flash Regions Table.

    :param ih: IntelHex object.
    :param row_end_address: Address where this row ends.
    :returns: RegionRow with the parsed data.
    """
    region_id = ihex.read_uint8(ih, row_end_address - ROW_OFFSET_ID)
    hash_type = ihex.read_uint8(ih, row_end_address - ROW_OFFSET_HASH_TYPE)
    start_page = ihex.read_uint16(ih, row_end_address - ROW_OFFSET_START_PAGE)
    length_bytes = ihex.read_uint32(ih, row_end_address - ROW_OFFSET_LENGTH)

    # Read hash data (8 bytes, but we only need the lower 4 bytes for pointer)
    hash_data_addr = row_end_address - ROW_OFFSET_HASH_DATA
    hash_data = ihex.read_uint32(ih, hash_data_addr)

    # If hash type is pointer, read the string it points to
    hash_pointer_data = ""
    if hash_type == RegionHashType.POINTER:
        hash_pointer_data = ihex.read_string(ih, hash_data)

    return RegionRow(
        id=region_id,
        start_page=start_page,
        length_bytes=length_bytes,
        hash_type=hash_type,
        hash_data=hash_data,
        hash_pointer_data=hash_pointer_data,
    )


def get_device_info_from_flash_regions(ih: IntelHex) -> DeviceInfo | None:
    """
    Extract DeviceInfo from Flash Regions Table in an IntelHex object.

    This is the primary detection method for micro:bit V2 MicroPython.

    :param ih: IntelHex object containing the hex data.
    :returns: DeviceInfo if valid Flash Regions Table is found, None otherwise.
    """
    header = _find_table_header(ih, DEVICE_SPECS[DeviceVersion.V2].page_size)
    if header is None:
        return None

    # Read all region rows
    regions: dict[int, RegionRow] = {}
    for i in range(header.region_count):
        row_end_address = header.start_address - i * ROW_SIZE
        row = _read_region_row(ih, row_end_address)
        regions[row.id] = row

    # Check for required regions
    if FlashRegionId.MICROPYTHON not in regions:
        return None
    if FlashRegionId.FILESYSTEM not in regions:
        return None

    micropython_region = regions[FlashRegionId.MICROPYTHON]
    fs_region = regions[FlashRegionId.FILESYSTEM]

    # Calculate addresses
    runtime_start = 0  # Always starts at 0
    runtime_end = header.end_address  # Table is at end of MicroPython region
    fs_start = fs_region.start_page * header.page_size
    fs_end = fs_start + fs_region.length_bytes
    version = micropython_region.hash_pointer_data

    return DeviceInfo(
        flash_page_size=header.page_size,
        flash_size=DEVICE_SPECS[DeviceVersion.V2].flash_size,
        flash_start_address=DEVICE_SPECS[DeviceVersion.V2].flash_start_address,
        flash_end_address=DEVICE_SPECS[DeviceVersion.V2].flash_size,
        runtime_start_address=runtime_start,
        runtime_end_address=runtime_end,
        fs_start_address=fs_start,
        fs_end_address=fs_end,
        micropython_version=version,
        device_version=DeviceVersion.V2,
    )

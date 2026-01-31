#!/usr/bin/env python3
"""
Filesystem reading and writing functionality.

This module provides functions to read and write files to the MicroPython
filesystem embedded in an Intel Hex file.
"""

from intelhex import IntelHex

from micropython_microbit_fs.device_info import DeviceInfo, DeviceVersion
from micropython_microbit_fs.exceptions import (
    FilesystemError,
    InvalidFileError,
    StorageFullError,
)

# =============================================================================
# Chunk Constants
# =============================================================================

CHUNK_SIZE = 128
"""Size of a filesystem chunk in bytes."""

CHUNK_DATA_SIZE = 126
"""Size of data that can be stored in a chunk (128 - 1 marker - 1 tail)."""

CHUNK_MARKER_SIZE = 1
"""Size of the chunk marker byte."""

MAX_CHUNKS = 252
"""Maximum number of chunks (256 - 4 reserved markers)."""

MAX_FILENAME_LENGTH = 120
"""Maximum length of a filename in bytes."""


class ChunkMarker:
    """Chunk marker byte values."""

    FREED = 0x00
    """Chunk has been freed but not erased."""

    PERSISTENT_DATA = 0xFD
    """Persistent data page marker (first byte of last FS page)."""

    FILE_START = 0xFE
    """Start of a file."""

    UNUSED = 0xFF
    """Empty/unused chunk."""


# =============================================================================
# Address Utilities
# =============================================================================


def chunk_index_to_address(chunk_index: int, fs_start: int) -> int:
    """Convert a 1-based chunk index to a flash address.

    :param chunk_index: The 1-based chunk index (1-252).
    :param fs_start: The filesystem start address in flash.
    :returns: The flash address where this chunk begins.
    """
    return fs_start + (chunk_index - 1) * CHUNK_SIZE


def address_to_chunk_index(address: int, fs_start: int) -> int:
    """Convert a flash address to a 1-based chunk index.

    :param address: The flash address.
    :param fs_start: The filesystem start address in flash.
    :returns: The 1-based chunk index.
    """
    return ((address - fs_start) // CHUNK_SIZE) + 1


def get_fs_start_address(device_info: DeviceInfo) -> int:
    """Get the effective filesystem start address.

    The filesystem may have more space available than needed. The start
    address is adjusted to ensure we don't exceed MAX_CHUNKS.

    :param device_info: Device information from the hex file.
    :returns: The effective filesystem start address.
    """
    fs_max_size = CHUNK_SIZE * MAX_CHUNKS
    fs_end = get_fs_end_address(device_info)

    # There might be more free space than the filesystem needs
    start_for_max_fs = fs_end - fs_max_size
    return max(device_info.fs_start_address, start_for_max_fs)


def get_fs_end_address(device_info: DeviceInfo) -> int:
    """Get the filesystem end address.

    For V1, we subtract one page for the magnetometer calibration data.

    :param device_info: Device information from the hex file.
    :returns: The filesystem end address.
    """
    end_address = device_info.fs_end_address

    # In V1 the magnetometer calibration data takes one flash page
    if device_info.device_version == DeviceVersion.V1:
        end_address -= device_info.flash_page_size

    return end_address


def get_last_page_address(device_info: DeviceInfo) -> int:
    """Get the address of the last filesystem page (persistent page).

    The last page is reserved for persistent data and not used for files.

    :param device_info: Device information from the hex file.
    :returns: The address where the last (persistent) page starts.
    """
    return get_fs_end_address(device_info) - device_info.flash_page_size


# =============================================================================
# Reading Files
# =============================================================================


def read_chunk(ih: IntelHex, address: int) -> bytes:
    """Read a full chunk from the Intel Hex at the given address.

    :param ih: The Intel Hex object.
    :param address: The start address of the chunk.
    :returns: The 128 bytes of the chunk.
    """
    return bytes(ih[address + i] for i in range(CHUNK_SIZE))


def read_files_from_hex(ih: IntelHex, device_info: DeviceInfo) -> dict[str, bytes]:
    """Read all files from the MicroPython filesystem.

    This scans the filesystem area for file start markers (0xFE), then
    follows the chunk chain to extract the complete file content.

    :param ih: The Intel Hex object containing MicroPython.
    :param device_info: Device information from the hex file.
    :returns: Dictionary mapping filenames to their content as bytes.
    :raises FilesystemError: If the filesystem structure is corrupted.
    """
    start_address = get_fs_start_address(device_info)
    end_address = get_last_page_address(device_info)

    # First pass: collect all used chunks and identify file starts
    used_chunks: dict[int, bytes] = {}
    start_chunk_indexes: list[int] = []

    chunk_addr = start_address
    chunk_index = 1

    while chunk_addr < end_address:
        chunk = read_chunk(ih, chunk_addr)
        marker = chunk[0]

        # Skip unused, freed, and persistent data chunks
        if marker not in (
            ChunkMarker.UNUSED,
            ChunkMarker.FREED,
            ChunkMarker.PERSISTENT_DATA,
        ):
            used_chunks[chunk_index] = chunk
            if marker == ChunkMarker.FILE_START:
                start_chunk_indexes.append(chunk_index)

        chunk_index += 1
        chunk_addr += CHUNK_SIZE

    # Second pass: follow chunk chains and extract file data
    files: dict[str, bytes] = {}
    seen_filenames: set[str] = set()

    for start_idx in start_chunk_indexes:
        start_chunk = used_chunks[start_idx]

        # Parse file header:
        # Byte 0: FILE_START marker (0xFE)
        # Byte 1: End offset in last chunk
        # Byte 2: Filename length
        # Bytes 3+: Filename
        end_offset = start_chunk[1]
        name_len = start_chunk[2]
        filename_bytes = start_chunk[3 : 3 + name_len]
        filename = filename_bytes.decode("utf-8")

        if filename in seen_filenames:
            raise FilesystemError(f"Found multiple files named: {filename}")
        seen_filenames.add(filename)

        # Follow chunk chain and collect data
        data = bytearray()
        current_chunk = start_chunk
        current_index = start_idx
        # In first chunk, data starts after header
        chunk_data_start = 3 + name_len

        # Track iterations to detect infinite loops
        max_iterations = len(used_chunks) + 1

        while max_iterations > 0:
            max_iterations -= 1
            next_index = current_chunk[CHUNK_SIZE - 1]  # Tail byte

            if next_index == ChunkMarker.UNUSED:
                # This is the last chunk - extract data up to end_offset
                data.extend(current_chunk[chunk_data_start : 1 + end_offset])
                break
            else:
                # Not the last chunk - extract all data bytes
                data.extend(
                    current_chunk[chunk_data_start : CHUNK_SIZE - 1]
                )  # All but tail

            # Move to next chunk
            next_chunk = used_chunks.get(next_index)
            if next_chunk is None:
                raise FilesystemError(
                    f"Chunk {current_index} points to unused index {next_index}"
                )

            # Verify the back-link
            if next_chunk[0] != current_index:
                raise FilesystemError(
                    f"Chunk index {next_index} did not link to "
                    f"previous chunk index {current_index}"
                )

            current_chunk = next_chunk
            current_index = next_index
            # After first chunk, data starts after the marker byte
            chunk_data_start = CHUNK_MARKER_SIZE

        if max_iterations <= 0:
            raise FilesystemError("Malformed file chunks did not link correctly")

        files[filename] = bytes(data)

    return files


# =============================================================================
# Writing Files
# =============================================================================


def calculate_file_size(filename: str, content: bytes) -> int:
    """Calculate the size in bytes a file will occupy in the filesystem.

    This returns the total number of bytes the file will use, which is
    always a multiple of the chunk size (128 bytes).

    :param filename: The name of the file.
    :param content: The file content as bytes.
    :returns: Size in bytes (always a multiple of 128).
    """
    filename_bytes = filename.encode("utf-8") if isinstance(filename, str) else filename
    header_size = 2 + len(filename_bytes)  # end_offset + name_len + name

    # Total data: header + content + trailing 0xFF byte
    total_data = header_size + len(content) + 1

    chunks_needed = (total_data + CHUNK_DATA_SIZE - 1) // CHUNK_DATA_SIZE
    return chunks_needed * CHUNK_SIZE


def get_free_chunks(ih: IntelHex, device_info: DeviceInfo) -> list[int]:
    """Get a list of free chunk indices in the filesystem.

    Scans the filesystem area and returns indices of chunks that are
    either unused (0xFF) or freed (0x00).

    :param ih: The Intel Hex object.
    :param device_info: Device information from the hex file.
    :returns: List of 1-based chunk indices that are free.
    """
    start_address = get_fs_start_address(device_info)
    end_address = get_last_page_address(device_info)

    free_chunks: list[int] = []
    chunk_addr = start_address
    chunk_index = 1

    while chunk_addr < end_address:
        marker = ih[chunk_addr]
        if marker == ChunkMarker.UNUSED or marker == ChunkMarker.FREED:
            free_chunks.append(chunk_index)
        chunk_index += 1
        chunk_addr += CHUNK_SIZE

    return free_chunks


def set_persistent_page(ih: IntelHex, device_info: DeviceInfo) -> None:
    """Set the persistent page marker in the last filesystem page.

    The last page of the filesystem is reserved for persistent data
    and is marked with a special marker byte.

    :param ih: The Intel Hex object to modify.
    :param device_info: Device information from the hex file.
    """
    last_page_addr = get_last_page_address(device_info)
    ih[last_page_addr] = ChunkMarker.PERSISTENT_DATA


def generate_file_header(filename: str, content: bytes) -> bytes:
    """Generate the file header bytes for the first chunk.

    The header contains:
    - Byte 0: end_offset (where data ends in last chunk)
    - Byte 1: filename length
    - Bytes 2+: filename

    :param filename: The name of the file.
    :param content: The file content.
    :returns: The header bytes to put in the first chunk's data area.
    """
    filename_bytes = filename.encode("utf-8")
    header_size = 2 + len(filename_bytes)  # end_offset + name_len + name

    # Calculate end_offset: where data ends in the last chunk (within data area)
    # This is (header_size + content_len) % CHUNK_DATA_SIZE
    # But we also add 1 trailing 0xFF byte like MicroPython does
    total_data = header_size + len(content)
    end_offset = total_data % CHUNK_DATA_SIZE

    header = bytearray(header_size)
    header[0] = end_offset
    header[1] = len(filename_bytes)
    header[2:] = filename_bytes

    return bytes(header)


def build_file_chunks(
    filename: str, content: bytes, free_chunks: list[int]
) -> tuple[list[tuple[int, bytes]], int]:
    """Build the chunk data for a file.

    Creates all the chunks needed to store the file, using the provided
    free chunk indices.

    :param filename: The name of the file.
    :param content: The file content.
    :param free_chunks: List of available chunk indices.
    :returns: Tuple of (list of (chunk_index, chunk_bytes), chunks_used)
    :raises InvalidFileError: If the filename is too long or empty.
    :raises StorageFullError: If there aren't enough free chunks.
    """
    # Validate file
    if not filename:
        raise InvalidFileError("File must have a filename")

    filename_bytes = filename.encode("utf-8")
    if len(filename_bytes) > MAX_FILENAME_LENGTH:
        raise InvalidFileError(
            f"Filename '{filename}' is too long "
            f"(max {MAX_FILENAME_LENGTH} bytes, got {len(filename_bytes)})"
        )

    if len(content) == 0:
        raise InvalidFileError(f"File '{filename}' must have content")

    # Build the full data stream: header + content + trailing 0xFF
    # MicroPython adds a trailing 0xFF when file fills exactly to chunk boundary
    header = generate_file_header(filename, content)
    fs_data = bytearray(len(header) + len(content) + 1)
    fs_data[: len(header)] = header
    fs_data[len(header) : len(header) + len(content)] = content
    fs_data[-1] = 0xFF

    # Calculate how many chunks we need
    chunks_needed = (len(fs_data) + CHUNK_DATA_SIZE - 1) // CHUNK_DATA_SIZE

    if chunks_needed > len(free_chunks):
        raise StorageFullError(
            f"Not enough space for file '{filename}'. "
            f"Need {chunks_needed} chunks, have {len(free_chunks)} free."
        )

    # Build the chunks
    result: list[tuple[int, bytes]] = []
    data_index = 0
    chunks_to_use = free_chunks[:chunks_needed]

    for i, chunk_idx in enumerate(chunks_to_use):
        chunk = bytearray(CHUNK_SIZE)
        # Fill with 0xFF first
        for j in range(CHUNK_SIZE):
            chunk[j] = 0xFF

        if i == 0:
            # First chunk: FILE_START marker
            chunk[0] = ChunkMarker.FILE_START
        else:
            # Continuation chunk: back-pointer to previous chunk
            chunk[0] = chunks_to_use[i - 1]

        # Copy data into the chunk's data area (bytes 1-126)
        data_end = min(len(fs_data), data_index + CHUNK_DATA_SIZE)
        data_to_copy = fs_data[data_index:data_end]
        chunk[CHUNK_MARKER_SIZE : CHUNK_MARKER_SIZE + len(data_to_copy)] = data_to_copy
        data_index = data_end

        # Set tail byte (next chunk index or 0xFF if last)
        if i < len(chunks_to_use) - 1:
            chunk[CHUNK_SIZE - 1] = chunks_to_use[i + 1]
        # else: already 0xFF

        result.append((chunk_idx, bytes(chunk)))

    return result, chunks_needed


def add_files_to_hex(
    ih: IntelHex,
    device_info: DeviceInfo,
    files: dict[str, bytes],
) -> None:
    """Write files to the MicroPython filesystem in an Intel Hex.

    Modifies the Intel Hex object in place to add the files to the
    filesystem region.

    :param ih: The Intel Hex object to modify.
    :param device_info: Device information from the hex file.
    :param files: Dictionary mapping filenames to their content as bytes.
    :raises InvalidFileError: If any file has invalid name or content.
    :raises StorageFullError: If the files don't fit in the filesystem.
    """
    if not files:
        return

    fs_start = get_fs_start_address(device_info)

    # Get all free chunks initially
    free_chunks = get_free_chunks(ih, device_info)

    if not free_chunks:
        raise StorageFullError("No storage space available in filesystem")

    # Write each file
    for filename, content in files.items():
        chunks, chunks_used = build_file_chunks(filename, content, free_chunks)

        # Write chunks to hex
        for chunk_idx, chunk_data in chunks:
            chunk_addr = chunk_index_to_address(chunk_idx, fs_start)
            for i, byte in enumerate(chunk_data):
                ih[chunk_addr + i] = byte

        # Remove used chunks from free list
        free_chunks = free_chunks[chunks_used:]

    # Set persistent page marker
    set_persistent_page(ih, device_info)

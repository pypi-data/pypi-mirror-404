#!/usr/bin/env python3
"""Intel Hex utilities for reading data from hex files."""

from io import StringIO

from intelhex import IntelHex


def load_hex(hex_data: str) -> IntelHex:
    """
    Load Intel Hex data from a string.

    :param hex_data: Intel Hex file content as a string.
    :returns: IntelHex object for accessing the data.
    """
    ih = IntelHex()
    ih.loadhex(StringIO(hex_data))
    return ih


def hex_to_string(ih: IntelHex) -> str:
    """
    Convert an IntelHex object back to a hex string.

    :param ih: IntelHex object.
    :returns: Intel Hex file content as a string.
    """
    output = StringIO()
    ih.write_hex_file(output)
    return output.getvalue()


def read_uint8(ih: IntelHex, address: int) -> int:
    """
    Read an unsigned 8-bit integer from the hex data.

    :param ih: IntelHex object.
    :param address: Address to read from.
    :returns: The byte value at the address.
    """
    return int(ih[address])


def read_uint16(ih: IntelHex, address: int, little_endian: bool = True) -> int:
    """
    Read an unsigned 16-bit integer from the hex data.

    :param ih: IntelHex object.
    :param address: Address to read from.
    :param little_endian: If True, use little-endian byte order (default: True).
    :returns: The 16-bit value at the address.
    """
    if little_endian:
        return int(ih[address] | (ih[address + 1] << 8))
    else:
        return int((ih[address] << 8) | ih[address + 1])


def read_uint32(ih: IntelHex, address: int, little_endian: bool = True) -> int:
    """
    Read an unsigned 32-bit integer from the hex data.

    :param ih: IntelHex object.
    :param address: Address to read from.
    :param little_endian: If True, use little-endian byte order (default: True).
    :returns: The 32-bit value at the address.
    """
    if little_endian:
        return int(
            ih[address]
            | (ih[address + 1] << 8)
            | (ih[address + 2] << 16)
            | (ih[address + 3] << 24)
        )
    else:
        return int(
            (ih[address] << 24)
            | (ih[address + 1] << 16)
            | (ih[address + 2] << 8)
            | ih[address + 3]
        )


def read_bytes(ih: IntelHex, address: int, length: int) -> bytes:
    """
    Read a sequence of bytes from the hex data.

    :param ih: IntelHex object.
    :param address: Start address to read from.
    :param length: Number of bytes to read.
    :returns: The bytes at the address range.
    """
    return bytes(ih[address + i] for i in range(length))


def read_string(ih: IntelHex, address: int, max_length: int = 256) -> str:
    """
    Read a null-terminated string from the hex data.

    :param ih: IntelHex object.
    :param address: Start address to read from.
    :param max_length: Maximum length to read (default 256).
    :returns: The string at the address (decoded as UTF-8).
    """
    chars = []
    for i in range(max_length):
        byte = ih[address + i]
        if byte == 0:
            break
        chars.append(byte)
    return bytes(chars).decode("utf-8", errors="replace")


def has_data_at(ih: IntelHex, address: int, length: int = 1) -> bool:
    """
    Check if the hex file has data at the specified address range.

    The intelhex library returns 0xFF for addresses without data,
    so we check if the address is within the actual data range.

    :param ih: IntelHex object.
    :param address: Start address to check.
    :param length: Number of bytes to check (default 1).
    :returns: True if there is data at all addresses in the range.
    """
    if not ih.minaddr() <= address <= ih.maxaddr():
        return False
    if not ih.minaddr() <= address + length - 1 <= ih.maxaddr():
        return False
    # Check if any address in range is in the actual data
    return any(addr in ih.addresses() for addr in range(address, address + length))

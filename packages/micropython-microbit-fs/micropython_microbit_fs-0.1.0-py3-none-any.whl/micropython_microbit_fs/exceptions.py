"""Custom exceptions for the micropython-microbit-fs library."""


class FilesystemError(Exception):
    """Base exception for filesystem-related errors."""

    pass


class InvalidHexError(FilesystemError):
    """Raised when the Intel Hex data is invalid or malformed."""

    pass


class NotMicroPythonError(FilesystemError):
    """Raised when the hex file does not contain MicroPython."""

    pass


class InvalidFileError(FilesystemError):
    """Raised when a file has invalid name or content."""

    pass


class StorageFullError(FilesystemError):
    """Raised when there is not enough space in the filesystem."""

    pass


class HexNotFoundError(Exception):
    """Raised when a requested hex file is not found."""

    pass

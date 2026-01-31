"""File representation for the MicroPython filesystem."""

from dataclasses import dataclass

from micropython_microbit_fs.exceptions import InvalidFileError
from micropython_microbit_fs.filesystem import calculate_file_size


@dataclass
class File:
    """
    Represents a file to be stored in the MicroPython filesystem.

    Attributes:
        name: The filename (max 120 characters, no path separators).
        content: The file content as bytes.
    """

    name: str
    content: bytes

    def __post_init__(self) -> None:
        """Validate file name and content."""
        if not self.name:
            raise InvalidFileError("Filename cannot be empty")
        if len(self.name) > 120:
            raise InvalidFileError(
                f"Filename too long: {len(self.name)} > 120 characters"
            )
        if not self.content:
            raise InvalidFileError("File content cannot be empty")

    @classmethod
    def from_text(cls, name: str, text: str, encoding: str = "utf-8") -> "File":
        """
        Create a File from text content.

        :param name: The filename.
        :param text: The text content.
        :param encoding: Text encoding (default: utf-8).
        :returns: A new File instance.
        """
        return cls(name=name, content=text.encode(encoding))

    def get_text(self, encoding: str = "utf-8") -> str:
        """
        Get the file content as text.

        :param encoding: Text encoding (default: utf-8).
        :returns: The file content as a string.
        """
        return self.content.decode(encoding)

    @property
    def size(self) -> int:
        """Return the size of the file content in bytes."""
        return len(self.content)

    @property
    def size_fs(self) -> int:
        """Return the total size the file consumes in the filesystem storage."""
        return calculate_file_size(self.name, self.content)

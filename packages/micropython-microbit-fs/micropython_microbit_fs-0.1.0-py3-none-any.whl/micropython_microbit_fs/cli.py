#!/usr/bin/env python3
"""
Command-line interface for micropython-microbit-fs.

This module provides CLI commands for working with micro:bit MicroPython
filesystems in Intel Hex files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

from cyclopts import App, Parameter

import micropython_microbit_fs as upyfs
from micropython_microbit_fs.exceptions import HexNotFoundError
from micropython_microbit_fs.hexes import (
    get_bundled_hex,
    list_bundled_versions,
)

app = App(
    name="microbit-fs",
    help="Inject and extract files from MicroPython Hex files for micro:bit.",
    version=upyfs.__version__,
)


@app.command
def info(hex_file: Path) -> None:
    """Display device and filesystem information from a MicroPython hex file.

    :param hex_file: Path to the Intel Hex file.
    """
    hex_data = hex_file.read_text()
    device_info = upyfs.get_device_info(hex_data)

    print(f"Device: micro:bit {device_info.device_version.value}")
    print(f"MicroPython version: {device_info.micropython_version}")
    print(f"Flash page size: {device_info.flash_page_size} bytes")
    print(f"Filesystem size: {device_info.fs_size} bytes")
    print(f"Filesystem start: 0x{device_info.fs_start_address:08X}")
    print(f"Filesystem end: 0x{device_info.fs_end_address:08X}")


@app.command(name="list")
def list_files(hex_file: Path) -> None:
    """List files stored in a MicroPython hex file.

    :param hex_file: Path to the Intel Hex file.
    """
    hex_data = hex_file.read_text()
    files = upyfs.get_files(hex_data)

    if not files:
        print("No files found in filesystem.")
        return

    total_size = sum(file.size for file in files)
    name_col_width = 40
    size_col_width = 12

    print(f"\n{'File':<{name_col_width}} {'Size':>{size_col_width}}")
    print(f"{'─' * name_col_width} {'─' * size_col_width}")
    for file in files:
        size_str = f"{file.size} bytes"
        print(f"{file.name:<{name_col_width}} {size_str:>{size_col_width}}")

    print(f"{'─' * name_col_width} {'─' * size_col_width}")
    total_str = f"{total_size} bytes"
    print(
        f"{'Total (' + str(len(files)) + ' files)':<{name_col_width}} {total_str:>{size_col_width}}"
    )


@app.command
def get(
    hex_file: Path,
    output_dir: Path = Path("."),
    filename: Optional[str] = None,
    force: bool = False,
) -> None:
    """Extract files from a MicroPython hex file.

    :param hex_file: Path to the Intel Hex file.
    :param output_dir: Directory to extract files to (default: current directory).
    :param filename: Extract only this specific file (default: extract all).
    :param force: Overwrite existing files without prompting (default: False).
    """
    hex_data = hex_file.read_text()
    files = upyfs.get_files(hex_data)

    if not files:
        print("No files found in filesystem.")
        return

    # Filter files if a specific filename was requested
    files_to_extract = files
    if filename is not None:
        files_to_extract = [f for f in files if f.name == filename]
        if not files_to_extract:
            raise SystemExit(f"Error: File not found in hex: {filename}")

    # Check for existing files before extracting (unless --force is used)
    if not force:
        existing_files = []
        for file in files_to_extract:
            output_path = output_dir / file.name
            if output_path.exists():
                existing_files.append(file.name)
        if existing_files:
            raise SystemExit(
                f"Error: Files already exist: {', '.join(existing_files)}\n"
                "Use --force to overwrite."
            )

    output_dir.mkdir(parents=True, exist_ok=True)

    for file in files_to_extract:
        output_path = output_dir / file.name
        output_path.write_bytes(file.content)
        print(f"Extracted: {file.name} ({file.size} bytes)")


@app.command
def add(
    files: list[Path],
    hex_file: Annotated[
        Optional[Path],
        Parameter(
            name="--hex-file",
            help="Path to input Intel Hex file. Required if --v1 or --v2 is not used.",
        ),
    ] = None,
    output: Optional[Path] = None,
    v1: Annotated[
        Optional[str],
        Parameter(
            help=(
                "Use bundled micro:bit V1 MicroPython hex. "
                "Specify a version (e.g., --v1=1.1) or 'latest' for the newest."
            ),
        ),
    ] = None,
    v2: Annotated[
        Optional[str],
        Parameter(
            help=(
                "Use bundled micro:bit V2 MicroPython hex. "
                "Specify a version (e.g., --v2=1.2) or 'latest' for the newest."
            ),
        ),
    ] = None,
) -> None:
    """Inject files into a MicroPython hex file.

    You must provide either --hex-file OR --v1/--v2 to specify the base hex file.

    **Examples:**

    - microbit-fs add main.py --v1=latest
    - microbit-fs add main.py --v2=1.2 --output my_program.hex
    - microbit-fs add main.py --hex-file micropython.hex
    - microbit-fs add main.py helper.py --hex-file micropython.hex --output output.hex

    :param files: One or more files to add to the filesystem.
    :param hex_file: Path to the input Intel Hex file.
    :param output: Output hex file path (default: <input_name>_output.hex).
    :param v1: Use bundled micro:bit V1 hex with specified version or 'latest'.
    :param v2: Use bundled micro:bit V2 hex with specified version or 'latest'.
    """
    has_hex_file = hex_file is not None
    has_v1 = v1 is not None
    has_v2 = v2 is not None
    if sum([has_hex_file, has_v1, has_v2]) == 0:
        raise SystemExit(
            "Error: You must provide a hex file or use --v1/--v2 for a bundled hex."
        )
    if sum([has_hex_file, has_v1, has_v2]) > 1:
        raise SystemExit(
            "Error: Cannot combine hex_file with --v1 or --v2, or use both --v1 and --v2."
        )

    hex_content: str
    try:
        # "latest" means use None to get the newest version
        if has_v1:
            version = None if v1.lower() == "latest" else v1  # type: ignore
            bundled_hex = get_bundled_hex(1, version)
            hex_content = bundled_hex.content
            resolved_version = version or bundled_hex.version
            hex_path = bundled_hex.file_path
            print(f"Using bundled micro:bit V1 MicroPython v{resolved_version}")
        elif has_v2:
            version = None if v2.lower() == "latest" else v2  # type: ignore
            bundled_hex = get_bundled_hex(2, version)
            hex_content = bundled_hex.content
            resolved_version = version or bundled_hex.version
            hex_path = bundled_hex.file_path
            print(f"Using bundled micro:bit V2 MicroPython v{resolved_version}")
        elif has_hex_file:
            hex_content = hex_file.read_text()  # type: ignore
            hex_path = hex_file  # type: ignore
    except HexNotFoundError as e:
        raise SystemExit(f"Error: {e}") from None

    file_objects = []
    for file_path in files:
        upy_file = upyfs.File(name=file_path.name, content=file_path.read_bytes())
        file_objects.append(upy_file)
        print(f"Adding: {file_path.name} ({upy_file.size_fs} bytes)")

    new_hex = upyfs.add_files(hex_content, file_objects)

    # Generate default output in cwd, filename: <name>_output.hex
    output_path = output if output else Path(f"{hex_path.stem}_output.hex")
    output_path.write_text(new_hex)
    print(f"Written to: {output_path.absolute().relative_to(Path.cwd())}")


@app.command
def versions() -> None:
    """List available bundled MicroPython hex versions.

    Shows all MicroPython versions bundled with this tool for both
    micro:bit V1 and V2.
    """
    versions_by_device = list_bundled_versions()

    print("Bundled MicroPython hex files:")
    for device_version in sorted(versions_by_device.keys()):
        print(f"\nmicro:bit V{device_version}:")
        for version in versions_by_device[device_version]:
            print(f"  - {version}")
        if len(versions_by_device[device_version]) == 0:
            print("  (none available)")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

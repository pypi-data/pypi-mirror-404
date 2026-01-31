# micropython-microbit-fs

[![Test](https://github.com/carlosperate/python-microbit-fs/actions/workflows/test.yml/badge.svg)](https://github.com/carlosperate/python-microbit-fs/actions/workflows/test.yml)
[![PyPI versions](https://img.shields.io/pypi/pyversions/micropython-microbit-fs.svg)](https://pypi.org/project/micropython-microbit-fs/)
[![PyPI - License](https://img.shields.io/pypi/l/micropython-microbit-fs.svg)](LICENSE)

A Python library and command line tool to inject and extract files from
[MicroPython](https://microbit-micropython.readthedocs.io)
Intel Hex file for the [BBC micro:bit](https://microbit.org).

## Features

- **Inject files** into a MicroPython hex file for flashing to micro:bit.
- **Extract files** from an existing micro:bit MicroPython hex file.
- **Get device info** from hex, including filesystem size and MicroPython version.
- **Command-line interface** for easy scripting and automation.
- Includes the latest MicroPython releases for micro:bit V1 and V2 boards.

## Installation

To install this terminal tool we recommend using [uv](https://docs.astral.sh/uv/):

```
uv tool install micropython-microbit-fs
```

It can also be installed via pip as a normal Python package:

```bash
pip install micropython-microbit-fs
```

## Command Line Interface

The package includes a `microbit-fs` command for working with hex files from
the terminal.

### Usage

Display device information:

```bash
$ microbit-fs info micropython.hex

Device: micro:bit V2
MicroPython version: micro:bit v2.1.2+0697c6d on 2023-10-30; MicroPython v1.18 on 2023-10-30
Flash page size: 4096 bytes
Filesystem size: 20480 bytes
Filesystem start: 0x0006D000
Filesystem end: 0x00073000
```

List files in a hex file:

```bash
$ microbit-fs list micropython_with_files.hex

File                                             Size
──────────────────────────────────────── ────────────
main.py                                     183 bytes
──────────────────────────────────────── ────────────
Total (1 files)                             183 bytes
```

Add files to a hex file:

```bash
# Add a single file using an existing MicroPython hex
microbit-fs add main.py --hex-file micropython.hex

# Add multiple files with a custom output file
microbit-fs add main.py helper.py --hex-file micropython.hex --output output.hex

# Use bundled micro:bit V1 MicroPython hex (latest version)
microbit-fs add main.py --v1=latest

# Use bundled micro:bit V2 MicroPython hex (latest version)
microbit-fs add main.py --v2=latest --output my_program.hex

# Use a specific MicroPython version
microbit-fs add main.py --v1=1.1.1 --output output.hex
microbit-fs add main.py --v2=2.1.2 --output output.hex
```

List available bundled MicroPython versions:

```bash
$ microbit-fs versions
Bundled MicroPython hex files:

micro:bit V1:
  - 1.1.1

micro:bit V2:
  - 2.1.2
```

Extract files from a hex file:

```bash
# Extract all files to the current directory
microbit-fs get micropython_with_files.hex

# Extract all files to a specific directory
microbit-fs get micropython_with_files.hex --output-dir ./extracted

# Extract a specific file
microbit-fs get micropython_with_files.hex --filename main.py

# Overwrite existing files without prompting
microbit-fs get micropython_with_files.hex --force
```


## Library Quick Start

### Add files to a MicroPython hex

```python
import micropython_microbit_fs as microbit_fs

# Read your MicroPython hex file
with open("micropython.hex") as f:
    micropython_hex = f.read()

# Create files to add
files = [
    microbit_fs.File.from_text("main.py", "from microbit import *\ndisplay.scroll('Hello!')"),
    microbit_fs.File.from_text("helper.py", "def greet(name):\n    return f'Hello {name}'"),
]

# Add files and get new hex string
new_hex = microbit_fs.add_files(micropython_hex, files)

with open("micropython_with_files.hex", "w") as f:
    f.write(new_hex)
```

### Get files from a MicroPython hex

```python
import micropython_microbit_fs as microbit_fs

# Read hex file with embedded files
with open("micropython_with_files.hex") as f:
    hex_data = f.read()

# Get all files
files = microbit_fs.get_files(hex_data)

for file in files:
    print(f"{file.name}: {file.size} bytes")
    print(file.get_text())
```

### Get device information

```python
import micropython_microbit_fs as microbit_fs

with open("micropython.hex") as f:
    hex_data = f.read()

info = microbit_fs.get_device_info(hex_data)
print(f"Device: micro:bit {info.device_version.value}")
print(f"MicroPython: {info.micropython_version}")
print(f"Filesystem size: {info.fs_size} bytes")
print(f"Flash page size: {info.flash_page_size} bytes")
```

### Use bundled MicroPython hex files

```python
import micropython_microbit_fs as microbit_fs

# List available bundled versions (dict keyed by device)
versions = microbit_fs.list_bundled_versions()
# {1: ['1.1.1'], 2: ['2.1.2']}
v1_versions = versions[1]
v2_versions = versions[2]

# Get the latest bundled hex for micro:bit V1
hex_data = microbit_fs.get_bundled_hex(1)

# Get a specific version
hex_data = microbit_fs.get_bundled_hex(2, "2.1.2")

# Add files to the bundled hex
files = [microbit_fs.File.from_text("main.py", "from microbit import *")]
new_hex = microbit_fs.add_files(hex_data, files)

with open("my_program.hex", "w") as f:
    f.write(new_hex)
```

## Development

This project uses [uv](https://docs.astral.sh/uv/) for project management.

### Setup

```bash
git clone https://github.com/carlosperate/python-microbit-fs.git
cd python-microbit-fs
uv sync --all-extras --dev
```

### Development Commands

This project includes a `make.py` script to automate common development tasks.

```bash
# Run all checks (lint, typecheck, format check, test with coverage)
uv run python make.py check

# Format code (ruff check --fix + ruff format)
uv run python make.py format

# Show all available commands
uv run python make.py help
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- This project has been ported (AI assisted) from the original
  [microbit-fs](https://github.com/microbit-foundation/microbit-fs)
  TypeScript library.
- This project packs the files inside a micro:bit MicroPython hex, which
  can then be flashed to a micro:bit.
  Alternatively, to read and write files from a running micro:bit device over
  USB, the [microFs](https://github.com/ntoll/microfs) CLI tool can be used.

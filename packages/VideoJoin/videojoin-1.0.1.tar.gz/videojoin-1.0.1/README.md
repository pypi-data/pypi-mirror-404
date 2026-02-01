# VideoJoin

## Overview

VideoJoin is a lightweight command-line tool for concatenating two video files (MP4, MOV, MKV, AVI, M4V) while preserving original audio and video quality using FFmpeg. It supports fast stream copying for compatible files and falls back to re-encoding for mismatches, making it ideal for quick edits without quality loss. As a Cython-optimized project, it leverages compiled extensions for efficient file scanning and subprocess handling, suitable for developers and users in media workflows .

This project follows a modular structure with source code in `src/VideoJoin/`, documentation in `docs/`, and build automation via `pyproject.toml` and `build.sh` for cross-platform compatibility (Linux, macOS, Windows with adjustments)   .

## Features

- Interactive selection of video files from the current directory.
- Automatic sorting and listing of eligible videos by name (case-insensitive).
- Lossless joining via FFmpeg concat (no re-encoding when possible).
- Fallback to high-quality re-encoding (libx264 CRF 18, AAC 192k) for incompatible formats.
- Temporary file handling with cleanup.
- FFmpeg dependency check on startup.
- Cython compilation for performance boosts in I/O operations  .

## Prerequisites

- Python 3.6+ (recommend 3.12 for Cython compatibility; use pyenv for isolation: `curl https://pyenv.run | bash`, then `pyenv install 3.12.0` and `pyenv shell 3.12.0`) .
- FFmpeg installed and in your PATH (download from https://ffmpeg.org/download.html).
- C compiler (e.g., gcc on Linux/macOS, Visual Studio on Windows) for Cython builds.
- Git for version control (recommended to initialize a repository and use `.gitignore` to exclude `__pycache__/`, `build/`, `*.so`, `.env`)    .

No additional pip packages are required beyond the standard library, but for development, consider `cython` via `pip install cython` in an isolated environment  .

## Installation

### From Source (Recommended for Development)

1. Clone or download the repository:
   ```
   git clone <repo-url>
   cd VideoJoin
   ```

2. Initialize Git if starting fresh (optional but recommended):
   ```
   git init
   ```

3. Set up `.gitignore` to exclude build artifacts and caches:
   ```
   # .gitignore content
   .env
   __pycache__/
   *.pyc
   *.pyo
   *.so
   build/
   ```
       .

4. Build and install in editable mode (handles Cython compilation):
   ```
   # Ensure pyenv or virtualenv for isolation
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install Cython if needed
   pip install cython

   # Build extensions
   chmod +x build.sh
   ./build.sh  # Or python setup.py build_ext --inplace if using setup.py

   # Editable install
   pip install -e .
   ```
   This compiles Cython files (e.g., `cli.pyx` if converted) into `.so` binaries in `build/lib/` and makes the package available as `VideoJoin`  .

### Via pip (Packaged Release)

Once published to PyPI (future), install directly:
```
pip3 install VideoJoin
```
This pulls from PyPI, installs dependencies (none beyond stdlib), and sets up the entry point for `videojoin` command or `python -m VideoJoin`  .

For requirements management, create `requirements.txt` with any dev tools:
```
cython
pytest  # For tests
```
Then `pip3 install -r requirements.txt` .

## Usage

### Command-Line Execution

Run the tool directly from the source directory:
```
python -m src.VideoJoin
```
Or after installation:
```
python -m VideoJoin
```
(If entry point is configured in `pyproject.toml`, use `videojoin` as a script.)

The tool will:
1. Scan the current folder for video files.
2. Prompt for selection of first and second video (prevents duplicates).
3. Ask for output filename (defaults to `{file1} + {file2}.mp4`).
4. Execute FFmpeg and report success/failure.

Example session:
```
Video Joiner – WITH ORIGINAL AUDIO (using ffmpeg)

Found video files:
  1. clip1.mp4
  2. clip2.mkv

Choose FIRST video → 1

Found video files:
  1. clip2.mkv

Choose SECOND video → 1

Output filename [clip1 + clip2.mp4]: joined.mp4

Joining with perfect audio sync:
   clip1.mp4
 + clip2.mkv
 → joined.mp4

Running ffmpeg (stream copy – no quality loss)…
SUCCESS! Perfectly joined with original sound → joined.mp4
```

For batch or advanced use, extend via importing `from VideoJoin.cli import main` in scripts .

### Building for Distribution

- Use `python -m build` to create wheels/sdists (configured in `pyproject.toml`).
- Cython outputs like `VideoJoin.cpython-312-x86_64-linux-gnu.so` go to `build/lib/` (gitignore them for clean repos)  .

## Project Structure

```
VideoJoin/
├── build.sh                  # POSIX build script for Cython
├── docs/                     # Documentation
│   ├── CHANGELOG.md
│   ├── folder-structure.md
│   └── VideoClip-spec.md
├── pyproject.toml            # Build config (setuptools/Cython)
├── README.md                 # This file
└── src/
    └── VideoJoin/
        ├── cli.py            # Core logic (Cython-compatible)
        ├── __init__.py       # Package init and version
        └── __main__.py       # Entry point
```
Add `tests/` for unit tests (e.g., `test_cli.py`) and `requirements-dev.txt` for tools like pytest   .

## Development

- **Folder Creation**: Use `mkdir -p src/VideoJoin docs tests` for extensions .
- **Logging/History**: The CLI uses print statements; extend with `inspect` for traceable calls if needed .
- **Testing**: Run `pytest tests/` after setup.
- **Versioning**: Update `__version__` in `__init__.py` and `CHANGELOG.md` per semantic rules .
- **License**: Add `LICENSE` (e.g., MIT) for open-source use .

## Troubleshooting

- **FFmpeg Not Found**: Install via package manager (e.g., `apt install ffmpeg` on Ubuntu) or download binaries.
- **Cython Build Errors**: Verify Python version with `which python3` and ensure C compiler; use `language_level=3` in directives .
- **Permission Issues**: On Unix, `chmod +x` scripts; use virtualenv to avoid global installs.
- **Cross-Platform**: Test paths with `pathlib`; avoid OS-specific assumptions .

For issues, check `CHANGELOG.md` or open a Git issue. Contributions welcome via pull requests after Git setup   .

## License

MIT License (add `LICENSE` file with standard text) .
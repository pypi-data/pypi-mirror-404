"""
SOURCEdefender PyInstaller Hook
===============================

This hook ensures PyInstaller correctly bundles all dependencies required by
SOURCEdefender when packaging applications that use encrypted .pye modules.

Why This Is Needed:
    PyInstaller performs static analysis to find imports, but SOURCEdefender's
    compiled Cython module (.so/.pyd) uses dynamic imports and ctypes calls
    that PyInstaller cannot detect. This hook explicitly lists all hidden
    imports so they are included in the final executable.

Categories of Hidden Imports:
    1. Core Dependencies - Required packages from requirements.txt
    2. Cryptography Stack - AES-GCM, HKDF, hashing modules
    3. SOURCEdefender Internal - The engine module itself
    4. Standard Library - Modules used by the security engine
    5. Anti-Debugging - ctypes, struct, signal for protection
    6. Platform-Specific - Windows registry access, etc.

Usage:
    This hook is automatically used when PyInstaller bundles an app that
    imports sourcedefender. You can also manually specify it:

        pyinstaller --additional-hooks-dir=. your_app.py

Maintenance:
    When adding new imports to engine.pyx, also add them here to ensure
    PyInstaller compatibility. Run 'sourcedefender pack' to verify.
"""

from PyInstaller.utils.hooks import get_hook_config, collect_data_files
import os

# Declares all dependencies used by SOURCEdefender's compiled .so files
# that PyInstaller cannot automatically detect

datas = []

hiddenimports = [
    # Core dependencies from requirements.txt
    "msgpack",
    "msgpack.exceptions",
    "feedparser",
    "cryptography",
    "cryptography.hazmat",
    "cryptography.hazmat.primitives",
    "cryptography.hazmat.primitives.ciphers",
    "cryptography.hazmat.primitives.ciphers.algorithms",
    "cryptography.hazmat.primitives.ciphers.modes",
    "cryptography.hazmat.primitives.ciphers.aead",
    "cryptography.hazmat.primitives.kdf",
    "cryptography.hazmat.primitives.kdf.pbkdf2",
    "cryptography.hazmat.primitives.kdf.hkdf",
    "cryptography.hazmat.primitives.hashes",
    "cryptography.hazmat.primitives.hmac",
    "cryptography.hazmat.backends",
    "cryptography.hazmat.backends.openssl",
    "boltons",
    "boltons.timeutils",
    "environs",
    "psutil",
    "ntplib",
    "requests",
    "requests.adapters",
    "requests.packages.urllib3.util.retry",
    "packaging",
    "packaging.version",
    "setuptools",
    "setuptools.command.easy_install",
    "wheel",
    "docopt",
    # SOURCEdefender internal modules
    "sourcedefender.engine",
    # Standard library modules used by SOURCEdefender
    "os",
    "sys",
    "datetime",
    "threading",
    "subprocess",
    "re",
    "gc",
    "marshal",
    "zlib",
    "hashlib",
    "inspect",
    "types",
    "importlib",
    "importlib.abc",
    "importlib.util",
    "ast",
    "textwrap",
    "logging",
    "pathlib",
    "tempfile",
    "glob",
    "shutil",
    "socket",
    # Crypto and encoding
    "base64",
    "uuid",
    # Network utilities
    "urllib3",
    "urllib3.exceptions",
    "urllib.request",
    "urllib.parse",
    "certifi",
    # Additional security-critical modules
    "platform",
    "time",
    "traceback",
    "warnings",
    "weakref",
    "copy",
    "collections",
    "itertools",
    "functools",
    # Anti-debugging protection modules
    "ctypes",
    "struct",
    "signal",
    "atexit",
    # Windows-specific modules
    "winreg",
    "_winreg",
    # PyInstaller integration
    "PyInstaller",
    "PyInstaller.__main__",
]

# Binary dependencies (if any)
binaries = []

# Runtime hooks for critical modules
runtime_hooks = []

"""
SOURCEdefender - Python Code Protection
=======================================

SOURCEdefender encrypts Python source files using AES-256-GCM encryption,
allowing encrypted .pye files to be imported transparently through Python's
import system.

Basic Usage:
    import sourcedefender  # Activates the import hook
    import my_encrypted_module  # Transparently decrypts and imports .pye files

CLI Commands:
    sourcedefender encrypt [--remove] <file.py>  # Encrypt Python files
    sourcedefender activate --token=<token>      # Activate license
    sourcedefender validate                      # Check license status

The engine module provides:
    - Encryption/decryption of Python source files
    - Import hooks for transparent .pye file loading
    - Security protections against reverse engineering
    - License management and activation

For more information, see: https://sourcedefender.co.uk

WARNING: DO NOT ADD CODE TO THIS FILE
=====================================
This file must remain minimal - only the import below.
All functionality lives in engine.pyx (compiled Cython module).
See CLAUDE.md "Package Entry Points" section for rationale.
"""
from . import engine

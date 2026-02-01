"""
SOURCEdefender Module Execution Entry Point
===========================================

This module enables running encrypted .pye files via:
    python -m sourcedefender script.pye

It also supports shebang execution:
    #!/usr/bin/env python -m sourcedefender

The import of engine triggers module-level code that detects
when argv[1] is a file and executes it via __defaults__.run().

CLI subcommands (encrypt, validate, activate, etc.) use the
console script entry point which calls engine.main() directly:
    sourcedefender encrypt --remove myfile.py

WARNING: DO NOT ADD CODE TO THIS FILE
=====================================
This file must remain minimal - only the import below.
The engine module's module-level code handles .pye execution.
CLI subcommands go through the console_scripts entry point.
See CLAUDE.md "Package Entry Points" section for rationale.
"""
from . import engine

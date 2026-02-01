## 16.0.43
- Fixed multiprocessing compatibility when encrypted modules are in the import chain.
- Added serialization support for functions from encrypted modules.

## 16.0.42
- Added account-scoped tracebacks for files encrypted with the same license account.

## 16.0.41
- Fixed staticmethod and classmethod decorators being stripped during code protection.

## 16.0.40
- Added thread safety for concurrent module imports.

## 16.0.39
- Removed unnecessary anonymous mmap restriction, enabling compatibility with polars and other libraries using memory-mapped arrays.
- Fixed corrupted license file crash during encryption - now handles gracefully instead of raising "Odd-length hex string" error.
- Fixed sys.modules identity assertion failure with C extensions.

## 16.0.38
- Fixed breaking libraries that use lazy-loading patterns during import.

## 16.0.37
- Fixed security vulnerability in module loader access controls.
- Fixed AttributeError propagation from encrypted modules

## 16.0.36
- Optimized import performance with directory contents caching.
- Added early exit for already-loaded modules in sys.modules.
- Improved negative cache with TTL-based expiration for dynamic file system changes.

## 16.0.35
- Improved exception handling for better interrupt signal support.
- Optimized checks by pre-computing module path comparisons.
- Code cleanup and maintenance.

## 16.0.34
- Refactored duplicate import protection.
- Optimized garbage collection.

## 16.0.33
- Optimized security check performance with improved caching mechanisms.
- Enhanced import performance for bulk module operations.
- Optimized file loading performance.

## 16.0.32
- Fixed compatibility issue with C extension imports.
- Improved package execution support for encrypted modules.
- Enhanced security for module loading operations.

## 16.0.31
- Added type validation for dictionary operations.

## 16.0.30
- Improved error handling.
- Fixed import system compatibility issues.

## 16.0.29
- Optimized PyInstaller integration.

## 16.0.28
- Improved error handling for module execution.

## 16.0.27
- Added account UUID verification for debugging restriction when allow_debugging is enabled.

## 16.0.26
- Improved error messages during encryption.

## 16.0.25
- Restored trial mode encryption functionality with 24-hour TTL enforcement.

## 16.0.24
- Optimized import performance for nested module imports.

## 16.0.23
- Optimized performance for plain-text Python code.

## 16.0.22
- Improved load performance.

## 16.0.21
- Optimized module import performance.

## 16.0.20
- Improved code maintainability by consolidating logic.

## 16.0.19
- Optimized import performance by caching debugger detection results to avoid redundant file I/O and system calls.
- Optimized frame inspection in `_is_internal_access()` by caching results and reducing max_depth from 25 to 15 frames.
- Improved `find_spec()` performance by leveraging cached internal access checks for importlib callers.

## 16.0.18
- Fixed AESGCM method type compatibility issue used by different cryptography library versions/platforms.
- Fixed double import of sourcedefender issues.

## 16.0.17
- Fixed AESGCM method type compatibility issue used by different cryptography library versions/platforms.
- Implemented full `allow_debugging` and `allow_tracebacks` license flag support. This allows developers with valid licenses to debug their encrypted code using standard debuggers.
- Improved corrupted license file handling

## 16.0.16
- Improved corrupted license file handling.
- Fixed UTF-8 encoding for all file operations.

## 16.0.15
- Fixed "Odd-length hex string" error during encryption when license file is corrupted - now automatically deletes corrupted license file, prompts user to re-activate, and exits (encryption requires a valid license file).
- Added module-level initialization guard to prevent re-initialization when sourcedefender is imported multiple times (handles cases where users accidentally include `import sourcedefender` in their code before encryption).
- Improved traceback protection to always filter SOURCEdefender frames even when tracebacks are allowed - protects internals while showing user code tracebacks for debugging.
- Improved error messages for corrupted .pye files to include the filename for easier debugging.
- Added Features section to validate command output showing enabled optional features (Debugging, Tracebacks).
- Optimized import performance by using cached flags for debugging and traceback checks.
- Simplified debugger detection: only license file controls debugging, no payload flags.
- Simplified traceback control: only license file controls tracebacks, no payload flags.

## 16.0.14
 - Improved serialization protection performance by scoping checks better.

## 16.0.13
- Refactored encrypted code execution to improve compatibility with third-party libraries.

## 16.0.12
- Fixed serialization protection to not interfere with normal JSON error handling and to properly support user-provided handlers.
- Added regression test for pandas file handle operations with contextmanager.

## 16.0.11
- Fixed JSON serialization errors for non-SOURCEdefender objects.

## 16.0.10
- Fixed serialization protection to properly support user-provided handlers for JSON and msgpack.
- User code can now use custom serialization handlers without interference from SDK protections.

## 16.0.9
- Fixed binascii.Error: Odd-length string when loading corrupted .pye files with invalid hex data.
- Added comprehensive error handling for base16 decoding errors (odd-length strings and other decode failures).
- Added test coverage for odd-length hex string handling in corrupted .pye file tests.

## 16.0.8
- Fixed UnboundLocalError when loading corrupted or older format .pye files.
- Fixed traceback protection to only wrap tracebacks containing SDK frames.
- Fixed traceback protection now correctly sanitizes output without interfering with standard Python operations.
- Fixed import aliases string length limitation.
- Added test coverage for corrupted .pye file handling and import alias functionality.

## 16.0.7
- Enhanced traceback protection with defensive fixes to prevent IndexError when libraries access traceback data.
- All protections now work correctly with PyTorch, pandas, numpy, miceforest, and other third-party libraries.

## 16.0.6
- Fixed exception formatting errors.

## 16.0.5
- Fixed TypeError when wrapping datetime.timezone and other datetime types in encrypted modules (datetime types cannot be subclassed).
- Fixed traceback leaks when wrapping non-subclassable types - exceptions during wrapping are now caught and handled gracefully.
- Refactored class wrapping mechanism to use type() instead of subclassing syntax for more robust handling of special types.
- Added test coverage for datetime.timezone support in encrypted modules.

## 16.0.4
- Fixed TypeError when wrapping Enum classes in encrypted modules (enums cannot be subclassed).
- Fixed TypeError when wrapping typing.Annotated and other typing special forms in encrypted modules.
- Added test coverage for Enum and typing.Annotated support in encrypted modules.

## 16.0.3
- Fixed Windows activation issue with User-Agent header containing carriage return character.
- Fixed license file loading security check to allow activation/validation on Windows.

## 16.0.2
- Refactor traceback protection code.

## 16.0.1
- Fix Pip install issue with docopt.
-
## 16.0.0
 - Major security architecture overhaul.
 - Replaced TgCrypto with the Cryptography library.
 - Refactor code to be FIPS 140-2 compliant.
 - New '.pye' file structure and formatting.
 - Improved macOS build system to generate universal binaries (Intel and ARM).
 - Removed SOURCEDEFENDER_SALT environment variable.
 - Removed '--salt' encrypt option.
 - Removed support for the getUrl() function.
 - Removed support for Python 3.9
 - Added support for Python 3.14

## 15.0.14
- Fixed shebang to work correctly.
- Fixed __name__ being __main__ in scripts

## 15.0.13
- Refactored System UUID Generation code.

## 15.0.12
- Added 'feedparser' to requirements.txt.
- Refactoring code.

## 15.0.11
- Refactored protection for overlay attacks.
- Updated documentation to include more details on our release process for CI/CD usage.

## 15.0.10
- Relaxed debugger detection in some cases.

## 15.0.9
- Added message when Debugger detected.

## 15.0.8
- Optimise Garbage Collection.

## 15.0.7
- Expanded dependencies list used by PyInstaller.
- Refactor code enabled via the '--debug' option.

## 15.0.6
- Added support for pushing to PyPi after build completes.

## 15.0.5
- Enabled (by default) the more secure method of using Python Bytecode as Payload data.
- Added opton (--no-bytecode) to disable the use of Python Bytecode as Payload data.

## 15.0.4
- Apply code formatting

## 15.0.3
- Exclude using Mac Address to identify machine inside a container.

## 15.0.2
- Force compilation of loaded code prior to execution.
- Include Mac Address when uniquly identifying a machine.

## 15.0.1
- Fixed issue where CLI command errors if no script is provided i.e python -m sourcedefender script.pye

## 15.0.0
- Dropped TgCrypto as has not been updated for 2 years (see: https://pypi.org/project/TgCrypto/#history)
- Added TgCrypto-pyrofork (see: https://pypi.org/project/TgCrypto-pyrofork/)

## 14.1.1
- Added '--debug' option to expose output from exceptions and tracebacks.
- Fixed issue where TTL wasn't converted to seconds.

## 14.1.0
- Enhanced error logging when incorrect salt/password is used.
- Added support for Python 3.13.
- Removed support for Python 3.8.

## 14.0.10
- Changed import error text when failing due to TTL expiration.

## 14.0.9
- Fix indentation bug in loader

## 14.0.8
- Adjusted retry algorithm for activations/validations.
- Refactored API client code.
- Adding NTP option to compare UTC offset to counter clock drift.

## 14.0.7
- Added feature to disbale auto_upgrades configured by the API.

## 14.0.6
- Updated PyPi documentation.

## 14.0.5
- Fixing bug in rate-limiting code.

## 14.0.4
- Added support for more granular rate-limiting of API access.

## 14.0.3
- Refactored protection for overlay attacks.

## 14.0.2
- Updated PyPi Documentation.
- Remove v8 Compatibility mode code that is no longer used.

## 14.0.1
- Added more checks for overlay attacks.
- Added SOURCEDEFENDER_INSERT_FINDER environment variable.
- Fix ttl parsing bug.

## 14.0.0
- Drop support for 32-bit Python on Windows AMD64 platforms.

## 13.0.1
- Refactored protection for overlay attacks.

## 13.0.0
- Refactored loader to improve speed.
- Removed zlib dependency.

## 12.0.5
- Fixed NoneType error in loader.

## 12.0.4
- Enhanced Garbage Collection to fix memory leak.

## 12.0.3
- Updated PyPi Docs to mirror Website.
- Updated versions listed in setup.py used by PyPi.
- Refactored code.

## 12.0.2
- Fixed bug where 'verify --target' returned wrong exit code.

## 12.0.1
- Refactored code.

## 12.0.0
- Renamed internal variables to fully block SourceRestorer on newly obfuscated code.
- Fixed a bug on activation returning an incorrect exit code on failure.

## 11.0.21
- Updated PyPi documentation.
- Impliment a fix for https://github.com/Lazza/SourceRestorer/

## 11.0.20
- Remove python-minifier support as it has stopped working.

## 11.0.19
- Updated Garbage Collection frequency.

## 11.0.18
- Updating PyPi documentation.

## 11.0.17
- Introduced minimum versions for Python dependencies we require.

## 11.0.16
- Updated missing 11.0.15 entry in the Changelog.

## 11.0.15
- Added --ttl-info option to provide message upon failed import due to TTL expiration.

## 11.0.14
- Set sys.dont_write_bytecode = True during import.

## 11.0.13
- Updated PyPi Docs.

## 11.0.12
- Moved auto-update to work every 10th day rather than on every use of the sdk tools.
- Remove Python 3.7 support as dependencies no longer install.

## 11.0.11
- Updated license validation code to fix bug with exit status.

## 11.0.10
- Moved the auto-upgrade test to be completed during a license verify and not on every run.

## 11.0.9
- Changed when the --target flag could be used.

## 11.0.8
- Added a '--target' flag to the validate option to view TTL data for encrypted files.
- Updated README documentation.

## 11.0.7
- Updated requirements.txt to remove dependencies that are not required.

## 11.0.6
- Fixed requirements.txt getting truncated.

## 11.0.5
- Added output of errors found by AST Parsing of plain-text code before encrypting.
- Removed parallel file encryption.
- Fixed bug that failed to set exit code to 1 when a file isn't encrypted.

## 11.0.4
- Dropped Linux/32bit-ARMv6 as dependency packages longer compile.

## 11.0.3
- Removed unrequired output during encryption.

## 11.0.2
- Updated PyPi README.md

## 11.0.1
- Updated supported Python versions for PyPi.

## 11.0.0
- Added in --bytecode option.
- Added support for Python 3.12.
- Removed support for Windows 32-bit Operating Systems.

## 10.0.13
- Fixed argparser bug when running as script.

## 10.0.12
- Fixed PyPi Upload issue.

## 10.0.11
- Fixed ValueError bug.

## 10.0.10
- Fixed UnboundLocalError bug.

## 10.0.9
- Enhanced licence validation code checking.

## 10.0.8
- Added support for Python 3.11.
- Added pyproject.toml

## 10.0.7
- Enabed the '--crossover' option by default prior to deprecating it.

## 10.0.6
- Updated Documentation on PyPi.
- Fixed 'validate' command so it works before activation.

## 10.0.5
- Updated PyPi Documentation in README.md.
- Fixed typo in '--help' section.

## 10.0.4
- Fixed bug where pack didn't work for trail users.
- Refactored pip installation code.

## 10.0.3
- Fixed wildcard import issue when using: 'from package import *' imports.

## 10.0.2
- Fixed crossover code detection error.

## 10.0.1
- Fixed bug in '--crossover'.

## 10.0.0
- Added '--crossover' as an option to enable cross Python version support.
- Changed auto-upgrade to keep sourcedefender in the current release branch e.g sourcedefender~=10.

## 9.4.2
- Changed defaults to '--minify' to keep Python annotations.

## 9.4.1
- Bugfixes

## 9.4.0
- Changed 'feedparser' & 'python-minifier' to get installed on-demand.
- Added '--minify' as an option rather than the default.
- Updated deployment process to include reviewing CHANGELOG.md before uploading to PyPi.
- Added 'changelog' to see changes since the last release.
- Added '--all' to the changelog option to view all changes, not just since the last release.
- Added CHANGELOG.md

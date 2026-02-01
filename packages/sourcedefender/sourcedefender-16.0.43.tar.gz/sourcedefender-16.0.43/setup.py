from struct import calcsize
from setuptools import setup
from os import path, chdir, getcwd, remove, listdir
from platform import machine, system
from sys import version_info, executable

chdir(path.abspath(path.dirname(__file__)))


def read(filename):
    try:
        with open(filename, 'rb') as fp:
            data = fp.read().decode('utf-8')
    except UnicodeDecodeError:
        with open(filename, 'r') as fp:
            data = fp.read()
    return data


def find_version(file_paths):
    version_file = read(file_paths)
    import re
    version_match = re.search(
        r"^##\s(.*)$",
        version_file,
        re.M,
    )
    if version_match:
        return version_match.group(1)

    raise RuntimeError(
        f"[find_version] Unable to find version string in {file_paths}. "
        f"Expected format: '## <version>' at the start of a line."
    )


def get_package_data_list():

    arch_bit = int(calcsize("P")*8)
    
    # Determine machine name - use "universal" for macOS to support both Intel and ARM
    if system().lower() == "darwin":
        machine_name = "universal"
    else:
        machine_name = machine().lower()

    if system().lower() == "linux":

        if machine().lower() == "x86_64":
            pass
            # ends_with = "linux-gnu.so"

        elif machine().lower() == "aarch64":
            pass

        # elif machine().lower().startswith("arm"):
        #     pass
            # machine_name = "armv6l"
            # ends_with = "arm-linux-gnueabihf.so"

    elif system().lower() == "windows":

        if machine().lower() == "amd64":
            pass
            # ends_with = "win_amd64.pyd"

    elif system().lower() == "darwin":
        pass
        # Universal build - machine_name already set above
    
    _find_all_files = ['__init__.py', '__main__.py']
    from os import walk, path, remove
    from shutil import copyfile, SameFileError
    path_to_check = path.join('src', 'ext', system().lower(
    ), machine_name, str(arch_bit), str(version_info.major) + str(version_info.minor))
    print("Path to check:", path_to_check)
    print("Current working directory:", path.abspath('.'))
    print("Path exists:", path.exists(path_to_check))
    print("Path isdir:", path.isdir(path_to_check))
    if path.isdir(path_to_check):
        for root, subfiles, files in walk(path_to_check):
            del subfiles
            for file in files:
                try:
                    copyfile(path.join(root, file), path.join('src', file))
                    _find_all_files.append(file)
                except SameFileError:
                    pass

        changelog = "CHANGELOG.md"
        if path.exists(changelog):
            try:
                copyfile(changelog, path.join('src', changelog))
                _find_all_files.append(changelog)
            except SameFileError:
                pass

    else:
        raise RuntimeError(
            f"\n\n[get_package_data_list] Extension directory not found\n"
            f"{'='*70}\n"
            f"Platform: {system().lower()}\n"
            f"Machine: {machine_name}\n"
            f"Architecture: {arch_bit}-bit\n"
            f"Python version: {version_info.major}.{version_info.minor}\n\n"
            f"This usually means we do not support your platform and architecture.\n"
            f"See https://pypi.org/project/sourcedefender/ for a list of supported platforms.\n\n"
            f"{'='*70}\n\n"
        )

    return _find_all_files


def get_requirements():
    requirements = []
    requirements.append("setuptools")
    try:
        with open("requirements.txt") as f:
            for P in f.readlines():
                # if P.lower().startswith("pyinstaller") and system().lower() == "darwin" and machine().lower() == "arm64":
                #    pass
                # else:
                requirements.append(P)
    except FileNotFoundError as e:
        raise RuntimeError(
            f"[get_requirements] requirements.txt file not found. "
            f"Current directory: {path.abspath('.')}. "
            f"Error: {e}"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"[get_requirements] Error reading requirements.txt: {e}"
        ) from e
    return requirements


def get_active_python_versions():
    """Return a list of active Python versions"""
    return ['3.10', '3.11', '3.12', '3.13', '3.14']


def get_python_requires():
    """Get python_requires from active versions"""
    active_versions = get_active_python_versions()
    if active_versions:
        return f">={active_versions[0]}"
    return ">=3.10"


def get_python_classifiers():
    """Get Python version classifiers from active versions"""
    active_versions = get_active_python_versions()
    return [f'Programming Language :: Python :: {version}' for version in active_versions]


try:
    setup(
        name="sourcedefender",
        version=find_version('CHANGELOG.md'),
        python_requires=f"!=2.*,{get_python_requires()}",
        description='Advanced encryption protecting your python codebase.',
        long_description=read(path.join(getcwd(), 'README.md')) + '\n',
        long_description_content_type="text/markdown",
        author='SOURCEdefender',
        author_email="hello@sourcedefender.co.uk",
        keywords="encryption source aes",
        packages=['sourcedefender'],
        package_dir={'sourcedefender': 'src'},
        package_data={'sourcedefender': get_package_data_list()},
        install_requires=list(get_requirements()),
        url="https://sourcedefender.co.uk/?src=pypi-url",
        project_urls={
            'Dashboard': 'https://dashboard.sourcedefender.co.uk/login?src=pypi-navbar',
        },
        license='Proprietary',
        entry_points={
            'console_scripts': [
                'sourcedefender = sourcedefender.engine:main',
            ]
        },
        options={
            'build_scripts': {
                'executable': executable,
            },
        },
        zip_safe=False,

        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            'Development Status :: 5 - Production/Stable',

            'Intended Audience :: Developers',
            'Intended Audience :: Education',
            'Intended Audience :: Information Technology',
            'Intended Audience :: Other Audience',
            'Intended Audience :: Science/Research',
            'Intended Audience :: System Administrators',

            'Topic :: Security',
            'Topic :: Security :: Cryptography',
            'Topic :: Software Development',
            'Topic :: Software Development :: Libraries',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: System :: Software Distribution',
            'Topic :: Utilities',

            'Operating System :: MacOS',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX :: Linux',


            *get_python_classifiers(),

            'Programming Language :: Python :: Implementation :: CPython'
        ],
    )
except RuntimeError:
    # Re-raise RuntimeError with context (already has context from our functions)
    raise
except Exception as e:
    # Wrap other exceptions with context
    raise RuntimeError(
        f"[setup] Unexpected error during setup() call: {type(e).__name__}: {e}\n"
        f"Current directory: {path.abspath('.')}\n"
        f"Please contact hello@sourcedefender.co.uk for assistance"
    ) from e

try:
    for file in get_package_data_list():
        if not file.endswith(".py"):
            full_path_file = path.join('src', file)
            if path.exists(full_path_file):
                try:
                    remove(path.join('src', file))
                except Exception as e:
                    # Don't fail setup if cleanup fails, but log it
                    print(
                        f"[cleanup] Warning: Failed to remove {full_path_file}: {e}")
except Exception as e:
    # Don't fail setup if cleanup fails, but log it
    print(f"[cleanup] Warning: Error during cleanup: {e}")

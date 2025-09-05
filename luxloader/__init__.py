"""This module deals with loading/downloading pyluxcore."""

import pathlib
import os
import itertools
import sys
import subprocess
import shutil
from textwrap import dedent
import base64
import hashlib

import bpy
import addon_utils


# The variable PYLUXCORE_VERSION specifies the release version of pyluxcore
# that will be downloaded from PyPi during the standard installation of
# BlendLuxCore. Only update this variable after the targeted version of
# pyluxcore has been released on PyPi.
PYLUXCORE_VERSION = "2.10.0"

# Check the location of this init file. The init file in the local dev folder
# returns only 'BlendLuxCore'
AM_IN_EXTENSION = __package__.startswith("bl_ext.")

# The environment variable BLC_DEV_PATH can be used to store a path to a local
# BlendLuxCore repository, which will then be imported
BLC_DEV_PATH = os.environ.get("BLC_DEV_PATH")

# The environment variable BLC_WHEEL_PATH can be used to store a path to a
# local pyluxcore wheel, which will then be installed
BLC_WHEEL_PATH = os.environ.get("BLC_WHEEL_PATH")

# TODO This is duplicated code with `utils` (but I could not import utils, because utils
# imports pyluxcore, which needs to be loaded by this module etc.
# Must break the circular ref...
ADDON_NAME = "BlendLuxCore"

def _get_module_name():
    """Get bl_idname for current addon."""
    components = __package__.split('.')
    prefix = list(itertools.takewhile(lambda x: x != ADDON_NAME, components))
    prefix.append(ADDON_NAME)
    return '.'.join(prefix)

def _get_user_dir(name):
    """Get a user writeable directory, create it if not existing."""
    return pathlib.Path(
        bpy.utils.extension_path_user(_get_module_name(), path=name, create=True)
    )


root_folder = _get_user_dir("")
assert(root_folder)
wheel_dl_folder = _get_user_dir("wheels")
wheel_backup_folder = _get_user_dir("wheels_backup")
wheel_dev_folder = _get_user_dir("pyluxcore_custom")

# For installation on PCs without internet, or in company networks where
# downloading with pip is an issue (reported cases), check for the presence of
# a folder install_offline/ where the pyluxcore wheel, and its dependencies,
# are placed.
# This takes precedence over BLC_WHEEL_PATH, as the latter still requires pip
# to work because of the dependencies.
install_offline_folder = root_folder / "install_offline"
if os.path.exists(install_offline_folder):
    BLC_OFFLINE_INSTALL = True
    BLC_WHEEL_PATH = None
else:
    BLC_OFFLINE_INSTALL = False
    # As an alternative to BLC_WHEEL_PATH as an environment variable, for more
    # user_friendly support: Check for the presence of one(!) development wheel
    # within the BlendLuxCore folder. This takes precedence over the
    # BLC_WHEEL_PATH environment variable.
    offline_files, *_ = os.walk(wheel_dev_folder)
    files_filtered = [
        f for f in offline_files[2] if f.startswith("pyluxcore") and f.endswith(".whl")
    ]  # TODO Why offline_files[2]? It is not iterable...
    if len(files_filtered) > 1:
        print(
            "[BLC] Warning: Content of 'pyluxcore_custom/' is not unique. "
            "Please delete all except one wheel file."
        )
    elif len(files_filtered) == 0:
        pass
    else:
        BLC_WHEEL_PATH = wheel_dev_folder / files_filtered[0]


def _execute_wheel_download(command):
    """Run a command (and specifically a download command)."""
    process = subprocess.run(
        command,
        capture_output=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    stdout = process.stdout
    stderr = process.stderr
    output = stdout.decode()
    error_output = stderr.decode()
    if output:
        print("[BLC] _download_wheel Output:\n", output)
    if error_output:
        print("[BLC] _download_wheel Errors:\n", error_output)

    if process.returncode:
        raise RuntimeError(
            f"[BLC] Failed to download LuxCore with return code {process.returncode}."
        ) from None


def _update_manifest():
    """Update blender_manifest, in order to make Blender download wheels."""
    # Setup manifest with wheel list
    manifest_path = (
        pathlib.Path(__file__).parent.parent.resolve() / "blender_manifest.toml"
    )
    manifest_files, *_ = os.walk(wheel_dl_folder)
    wheels = [pathlib.Path(wheel_dl_folder, f).as_posix() for f in manifest_files[2]]
    wheel_statement = f"wheels = {wheels}\n"

    with open(manifest_path, "r", encoding="utf-8") as file_handler:
        manifest = list(file_handler)
    with open(manifest_path, "w", encoding="utf-8") as file_handler:
        for line in manifest:
            if line.startswith("## WHEELS ##"):
                file_handler.write(wheel_statement)
            elif line.strip().startswith("wheels ="):
                file_handler.write(wheel_statement)
            else:
                file_handler.write(line)


def _save_installation_info(whl_hash="None", plc_version="None"):
    """Save information from the last installation.

    Only one of the supplied arguments should be different from 'None'
    to ensure that the type of installation is saved implicityly as well.
    """
    info_file = root_folder / "pyluxcore_installation_info.txt"
    header_text = dedent(
        """\
        # This file is used to store information about the pyluxcore installation.
        # It is used to determine whether a new installation is necessary at each startup.
        # Only one entry should be different from 'None', it indicates from which source
        # the installation was taken.
        #
        # The file is automatically generated and should not be edited manually.\n
    """
    )
    with open(info_file, "w", encoding="utf-8") as f:
        f.write(header_text)
        f.write(f"wheel-hash: {whl_hash}\n")
        f.write(f"pyluxcore-version: {plc_version}\n")


def _get_installation_info():
    """Check if the version to be installed matches the descritption saved during
    the last install.

    If it matches, installation is skipped for efficiency.
    """
    # read the file
    info_file = root_folder / "pyluxcore_installation_info.txt"
    print(f"[BLC] Checking {info_file}")

    if not os.path.exists(info_file):
        return "None", "None"

    with open(info_file, "r", encoding="utf-8") as f:
        old_wheel_hash = None
        old_pyluxcore_version = None
        for line in f.readlines():
            line = line.strip()
            if line.startswith("#"):  # comments
                pass
            elif line.startswith("wheel-hash:"):
                old_wheel_hash = line.split(":")[1].strip()
            elif line.startswith("pyluxcore-version:"):
                old_pyluxcore_version = line.split(":")[1].strip()
            else:
                pass

    return old_wheel_hash, old_pyluxcore_version


def _clear_wheels():
    """Remove wheel files from wheel folder."""
    files = os.listdir(wheel_dl_folder)
    if len(files) == 0:
        return
    for file in files:
        os.remove(wheel_dl_folder / file)


def _backup_wheels():
    """Backup any wheels from a previously successful installation."""
    files = os.listdir(wheel_dl_folder)
    if len(files) == 0:
        return
    for file in files:
        shutil.move(wheel_dl_folder / file, wheel_backup_folder / file)


def _delete_backup_wheels():
    """Remove all backup wheels from previously successful installation."""
    files = os.listdir(wheel_backup_folder)
    if len(files) == 0:
        return
    for file in files:
        os.remove(wheel_backup_folder / file)


def _restore_backup_wheels():
    """Remove backup wheels from previously successful installation in wheel folder."""
    files = os.listdir(wheel_backup_folder)
    if len(files) == 0:
        return
    for file in files:
        shutil.move(wheel_backup_folder / file, wheel_dl_folder / file)


def _check_offline_content():
    """Check if offline folder contains something to install."""
    files = os.listdir(install_offline_folder)
    if len(files) == 0:
        raise RuntimeError(
            "BlendLuxCore Installation Error: "
            "The install_offline/ directory exists but is empty!"
        )
    for file in files:
        if file.startswith("pyluxcore"):
            pyluxcore_version = file.split("-")[1]
            return pyluxcore_version
    return None  # no valid file was found


def _copy_offline_files():
    """Copy offline folder content to wheel folder."""
    files = os.listdir(install_offline_folder)
    for file in files:
        shutil.copy(install_offline_folder / file, wheel_dl_folder / file)


def delete_install_offline():
    """Clear offline folder content."""
    files = os.listdir(install_offline_folder)
    for file in files:
        os.remove(install_offline_folder / file)
    os.rmdir(install_offline_folder)


def download_pyluxcore():
    """Download and install pyluxcore wheel and dependencies."""
    # We cannot 'pip install' directly, as it would install pyluxcore system-wide
    # instead of in Blender environment
    # Blender has got its own logic for wheel installation, we'll rely on it

    # Step 0: for offline install, check content of install_offline/ folder,
    # derive pyluxcore_version from content, copy files to wheels/ folder
    # and skip the rest.
    if BLC_OFFLINE_INSTALL:
        pyluxcore_version = _check_offline_content()
        _clear_wheels()
        _copy_offline_files()
        _update_manifest()
        _save_installation_info("None", pyluxcore_version)
        return 0

    pyluxcore_version = PYLUXCORE_VERSION

    # Step 1: get installation info for comparison in the following steps
    old_wheel_hash, old_pyluxcore_version = _get_installation_info()

    # Step 2: If BLC_WHEEL_PATH is specified, install that
    if BLC_WHEEL_PATH:
        with open(BLC_WHEEL_PATH, "rb") as wheel_file:
            wheel_hash = (
                base64.urlsafe_b64encode(
                    hashlib.sha256(wheel_file.read()).digest()
                )
                .decode("latin1")
                .rstrip("=")
            )
        if wheel_hash == old_wheel_hash:
            print(
                "[BLC] skipping pyluxcore installation. "
                "Custom wheel matching hash already installed."
            )
            return 2
        print("[BLC] Installing local version of pyluxcore")
        command = [
            sys.executable,
            "-m",
            "pip",
            "download",
            BLC_WHEEL_PATH,
            "-d",
            wheel_dl_folder,
        ]
        try:
            _backup_wheels()
            _execute_wheel_download(command)
            _update_manifest()
            _delete_backup_wheels()
            _save_installation_info(wheel_hash, "None")
            return 0
        except Exception as err:
            print(f"[BLC] Unexpected {err=}, {type(err)=}")
            _clear_wheels()
            _restore_backup_wheels()
            return 1

    # Step 3: If pyluxcore_version is specified, install that
    elif pyluxcore_version:
        if pyluxcore_version.strip() == old_pyluxcore_version.strip():
            print(
                "[BLC] Skipping pyluxcore installation. "
                "Specified version already installed."
            )
            return 2
        print("[BLC] Installing pyluxcore version:", pyluxcore_version)
        command = [
            sys.executable,
            "-m",
            "pip",
            "download",
            f"pyluxcore=={pyluxcore_version}",
            "-d",
            wheel_dl_folder,
        ]
        try:
            _backup_wheels()
            _execute_wheel_download(command)
            _update_manifest()
            _delete_backup_wheels()
            _save_installation_info("None", pyluxcore_version)
            return 0
        except Exception as err:
            print(f"[BLC] Unexpected {err=}, {type(err)=}")
            _clear_wheels()
            _restore_backup_wheels()
            return 1

    # Step 4: Fallback, none of the above specified
    print(
        "[BLC] ERROR: neither BLC_WHEEL_PATH nor PYLUXCORE_VERSION specified "
        "in function download_pyluxcore()!"
    )
    return 1


def ensure_pyluxcore():
    """Ensure that pyluxcore is installed."""
    # Load/download pyluxcore
    if AM_IN_EXTENSION:
        # We'll invoke download_pyluxcore at each init
        # We rely on pip local cache for this call to be transparent,
        # after the wheels have been downloaded once, unless an update is required
        download_status = download_pyluxcore()
        if download_status == 0:
            # Ask Blender to do the install
            addon_utils.extensions_refresh(ensure_wheels=True)
        elif download_status == 1:
            # There was an error during download
            print(
                "[BLC] WARNING: Download of pyluxcore not successful... "
                "Import will be attempted, but may be unsuccessful..."
            )
        elif download_status == 2:
            # The version to be downloaded was already installed. Nothing to do.
            pass
        else:
            # Unknown error
            print(
                "[BLC] WARNING: Unknown return code received from download_pyluxcore()... "
                "Import will be attempted, but may be unsuccessful..."
            )

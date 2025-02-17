import tempfile
import platform
import os
import sys
import subprocess
from shutil import which
import shutil
import pathlib
import json
import requests

import bpy
import addon_utils

if bpy.app.version < (2, 93, 0):
    raise Exception("\n\nUnsupported Blender version. 2.93 or higher is required by BlendLuxCore.")

if platform.system() == "Darwin":
    if bpy.app.version < (4, 2, 0):
        raise Exception("\n\nUnsupported Blender version. 4.2 or higher is required.")
    mac_version = tuple(map(int, platform.mac_ver()[0].split(".")))
    if mac_version < (10, 9, 0):
        raise Exception("\n\nUnsupported Mac OS version. 10.9 or higher is required.")

if platform.system() in {"Linux", "Darwin"}:
    # Required for downloads from the LuxCore Online Library
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

bl_info = {
    "name": "LuxCoreRender",
    "author": "Simon Wendsche (B.Y.O.B.), Michael Klemm (neo2068), Odilkhan Yakubov (odil24), acasta69, u3dreal, Philstix",
    "version": (2, 9),
    "blender": (4, 2, 0),
    "category": "Render",
    "description": "LuxCoreRender integration for Blender",
    "warning": "alpha4",

    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}
version_string = f'{bl_info["version"][0]}.{bl_info["version"][1]}{bl_info["warning"]}'

# The environment variable BLC_WHEEL_PATH can be used to store a path
# to a local pyluxcore wheel, which will then be installed
blc_wheel_path = os.environ.get("BLC_WHEEL_PATH")
# The environment variable BLC_DEV_PATH can be used to store a path
# to a local BlendLuxCore repository, which will then be imported
blc_dev_path = os.environ.get("BLC_DEV_PATH")
# Check the location of this init file. The init file in the local dev folder returns only 'BlendLuxCore'
am_in_extension = __name__.startswith("bl_ext.")

root_folder = pathlib.Path(__file__).parent.resolve()
wheel_folder =  root_folder / "wheels"

if am_in_extension:
    def _get_platform_info():
        # Get the current Python version and architecture
        python_version = sys.version_info
        python_version_str = f"cp{python_version.major}{python_version.minor}"
        architecture = None
        machine = None
        if platform.system() == "Darwin":
            architecture = "macosx_"
            machine = platform.machine()
        elif platform.system() == "Linux":
            architecture = "manylinux_"
            machine = "x86_64"
        elif platform.system() == "Windows":
            architecture = "win_" # including the underscore just to be safe this never pops up elsewhere in the future, 'win' is a pretty short string and common term
            machine = "amd64"

        return architecture, machine, python_version_str

    def _get_pypi_latest(architecture, machine, python_version_str):
        # Fetch package metadata from PyPI
        url = f"https://pypi.org/pypi/pyluxcore/json"
        try:
            response = requests.get(url)
            if response.status_code != 200:
                # Other errors
                print("WARNING: Fetching information from PyPi returned non-normal error with error-code", response.status_code)
                return None
        except:
            # In case of issues getting the json, e.g. because there is no internet connection
            print("WARNING: Failed to fetch information from PyPi. Possibly the result of a missing internet connection.")
            return None

        # Extract latest version of the package
        metadata = response.json()
        releases = metadata["releases"]
        versions = reversed(list(releases.keys())) # sort from newest to oldest
        for version in versions:
            for file in releases[version]:
                if file["yanked"]:
                    continue
                fname = file["filename"]
                if fname.endswith(".whl"):
                    wheel_filename = fname
                    if python_version_str in file["python_version"] and architecture in fname and machine in fname:
                        return wheel_filename
        print("WARNING: No pyluxcore wheel matching the local platform information was found on PyPi!")
        return None

    def _is_wheel_present(wheel_filename):
        wheel_path = os.path.join(wheel_folder, wheel_filename)
        if os.path.exists(wheel_path):
            return True
        return False

    def _search_manifest_wheels():
        # Search manifest for statement of last used wheel (or: wheels including dependencies)
        wheel_list = None
        manifest_path = root_folder / "blender_manifest.toml"
        with open(manifest_path, "r") as fp:
            manifest = list(fp)
            for line in manifest:
                if line.strip().startswith("wheels ="):
                    # extract the pure wheel names
                    wheel_list = line.split('[')[1].strip().rstrip(']').split(',')
                    wheel_list = [w.strip().strip().strip('"').strip("'").split('/')[1] for w in wheel_list] # strip both " and ' characters because either may be valid
        return wheel_list

    def _execute_wheel_install(command):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        output = stdout.decode()
        error_output = stderr.decode()
        if output:
            print("Output:\n", output)
        if error_output:
            print("Errors:\n", error_output)

        if process.returncode:
            raise RuntimeError(
                f'Failed to download LuxCore with return code {process.returncode}.'
            ) from None

        # Setup manifest with wheel list
        manifest_path = root_folder / "blender_manifest.toml"
        files, *_ = os.walk(wheel_folder)
        wheels = [
            pathlib.Path(".", "wheels", f).as_posix()
            for f in files[2]
        ]
        wheel_statement = f"wheels = {wheels}\n"

        with open(manifest_path, "r") as fp:
            manifest = list(fp)
        with open(manifest_path, "w") as fp:
            for line in manifest:
                if line.startswith("## WHEELS ##"):
                    fp.write(wheel_statement)
                elif line.strip().startswith("wheels ="):
                    fp.write(wheel_statement)
                else:
                    fp.write(line)

    def install_pyluxcore():
        # We cannot 'pip install' directly, as it would install pyluxcore system-wide
        # instead of in Blender environment
        # Blender has got its own logic for wheel installation, we'll rely on it

        # Step 1: If BLC_WHEEL_PATH is specified, install that and skip the rest
        if blc_wheel_path:
            print()
            print('~'*43)
            print('~ USING LOCAL VERSION OF pyluxcore ~')
            print('~'*43)
            print()
            command = [
                sys.executable,
                '-m',
                'pip',
                'download',
                blc_wheel_path,
                '-d',
                wheel_folder,
            ]
            _execute_wheel_install(command)
            return True

        # Step 2: Check if platform information is complete and valid
        architecture, machine, python_version_str = _get_platform_info()
        print('Platform information:', architecture, machine, python_version_str)
        if architecture is None or machine is None or python_version_str is None:
            # In this case, just hope pyluxcore was previously installed and can be imported. Else error will be raised below so do nothing here at the moment.
            print("WARNING: Platform information is incomplete")
            return False

        # Step 3: Try to get latest wheel information from PyPi
        wheel_filename = _get_pypi_latest(architecture, machine, python_version_str)
        print("PyPi Information result:", wheel_filename)

        # Step 4.1: If wheel information available, check if already present, else download
        if wheel_filename is not None:
            pyluxcore_downloaded = _is_wheel_present(wheel_filename)
            if pyluxcore_downloaded:
                print('Download of pyluxcore skipped, latest version was found on system')
                return True
            else:
                try:
                    # Download wheel
                    print('Downloading pyluxcore')
                    command = [
                        sys.executable,
                        '-m',
                        'pip',
                        'download',
                        'pyluxcore',
                        '-d',
                        wheel_folder
                    ]
                    _execute_wheel_install(command)
                    return True
                except:
                    print("WARNING: Identified a latest version of pyluxcore from PyPi but could not download!")
                    print("Attempting to use previously installed version instead...")

        # Step 4+.2: If wheel information missing, check if a version is defined in the manifest and if it is present locally
        print('Searching manifest...')
        wheel_list = _search_manifest_wheels()
        print('wheel list: ')
        print(wheel_list)
        if wheel_list is None:
            print('WARNING: No pyluxcore result in manifest!')
            # In this case, just hope pyluxcore was previously installed and can be imported. Else error will be raised below so do nothing here at the moment.
            return False
        all_wheels_present = True
        for wheel in wheel_list:
            all_wheels_present = all_wheels_present and _is_wheel_present(wheel)
        if all_wheels_present:
            return True

        # Ultimately:
        # In this case, just hope pyluxcore was previously installed and can be imported. Else error will be raised below so do nothing here at the moment.
        return False
            
    # We'll invoke install_pyluxcore at each init
    # We rely on pip local cache for this call to be transparent, after the wheels
    # have been downloaded once, unless an update is required
    install_success = install_pyluxcore()
    if not install_success:
        print('WARNING: Check for pyluxcore not successful... Import will be attempted, but may be unsuccessful...')

    # Ask Blender to do the install
    addon_utils.extensions_refresh(ensure_wheels=True)

    try:
        import pyluxcore
    except ImportError as error:
        msg = "\n\nCould not import pyluxcore."
        # Raise from None to suppress the unhelpful
        # "during handling of the above exception, ..."
        raise RuntimeError(msg + "\n\nImportError: %s" % error) from None

if blc_dev_path and am_in_extension:
    print()
    print('~'*43)
    print('~ USING LOCAL DEV VERSION OF BlendLuxCore ~')
    print('~'*43)
    print()
    sys.path.insert(0, blc_dev_path)
    from BlendLuxCore import *
else:
    from . import properties, engine, handlers, operators, ui, nodes, utils
    from .utils.log import LuxCoreLog

def register():
    engine.register()
    handlers.register()
    operators.register()
    properties.register()
    ui.register()
    nodes.register()
    
    pyluxcore.Init(LuxCoreLog.add)
    print(f"BlendLuxCore (wheels) {version_string} registered (with pyluxcore {pyluxcore.Version()})")

def unregister():
    engine.unregister()
    handlers.unregister()
    operators.unregister()
    properties.unregister()
    ui.unregister()
    nodes.unregister()

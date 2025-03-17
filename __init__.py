import platform
import os
import sys
import subprocess
import shutil
import pathlib
import requests
import hashlib
import base64

import bpy
import addon_utils

# Check firts if Blender and OS versions are compatible
if bpy.app.version < (4, 2, 0):
    raise Exception("\n\nUnsupported Blender version. 4.2 or higher is required by BlendLuxCore.")

if platform.system() == "Darwin":
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

_PYLUXCORE_VERSION = '2.9a1.post14' # for a release
# _PYLUXCORE_VERSION = None # For automatic download of latest from PyPi

# Check the location of this init file. The init file in the local dev folder returns only 'BlendLuxCore'
am_in_extension = __name__.startswith("bl_ext.")

if am_in_extension:
    root_folder = pathlib.Path(__file__).parent.resolve()
    wheel_dl_folder =  root_folder / "wheels" # for wheels download
    if not os.path.exists(wheel_dl_folder):
        os.makedirs(wheel_dl_folder)
    wheel_backup_folder =  root_folder / "wheels_backup" # backup of downloaded wheels
    if not os.path.exists(wheel_backup_folder):
        os.makedirs(wheel_backup_folder)
    wheel_dev_folder =  root_folder / "pyluxcore_custom" # folder where a nightly build pyluxcore wheel can be placed
    if not os.path.exists(wheel_dev_folder):
        os.makedirs(wheel_dev_folder)

    # The environment variable BLC_DEV_PATH can be used to store a path
    # to a local BlendLuxCore repository, which will then be imported
    blc_dev_path = os.environ.get("BLC_DEV_PATH")

    # The environment variable BLC_WHEEL_PATH can be used to store a path
    # to a local pyluxcore wheel, which will then be installed
    blc_wheel_path = os.environ.get("BLC_WHEEL_PATH")

    # As an alterniative for more user_friendly support:
    # Check for the presence of one(!) development wheel within the BlendLuxCore folder
    # This takes precedence over the BLC_WHEEL_PATH environment variable
    files, *_ = os.walk(wheel_dev_folder)
    if len(files[2]) > 1:
        print("[BLC] Warning: Content of 'pyluxcore_custom/' is not unique. Please delete all except one wheel file.")
    elif len(files[2]) == 0:
        pass
    else:
        blc_wheel_path = wheel_dev_folder / files[2][0]

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
                print("[BLC] WARNING: Fetching information from PyPi returned non-normal error with error-code", response.status_code)
                print("[BLC] pyluxcore installation will be skipped. If pyluxcore is not already installed, import will fail.")
                return None
        except:
            # In case of issues getting the json, e.g. because there is no internet connection
            print("[BLC] WARNING: Failed to fetch information from PyPi. Possibly the result of a missing internet connection.")
            print("[BLC] pyluxcore installation will be skipped. If pyluxcore is not already installed, import will fail.")
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
        print("[BLC] WARNING: No pyluxcore wheel matching the local platform information was found from PyPi docs!")
        print("[BLC] pyluxcore installation will be skipped. If pyluxcore is not already installed, import will fail.")
        return None

    def _execute_wheel_download(command):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
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

        # Setup manifest with wheel list
        manifest_path = root_folder / 'blender_manifest.toml'
        files, *_ = os.walk(wheel_dl_folder)
        wheels = [
            pathlib.Path('.', 'wheels', f).as_posix()
            for f in files[2]
        ]
        wheel_statement = f'wheels = {wheels}\n'

        with open(manifest_path, 'r') as fp:
            manifest = list(fp)
        with open(manifest_path, 'w') as fp:
            for line in manifest:
                if line.startswith('## WHEELS ##'):
                    fp.write(wheel_statement)
                elif line.strip().startswith('wheels ='):
                    fp.write(wheel_statement)
                else:
                    fp.write(line)

    def _save_installation_info(whl_hash='None', plc_version='None', pypi_name='None'):
        # Save the has of the pyluxcore.pyd file for comparison at next startup
        # Only one of the supplied arguments should be different from 'None'
        # to ensure that the type of installation is saved implicityly as well
        info_file = root_folder / 'pyluxcore_installation.txt'
        with open(info_file, 'w') as f:
            f.write(whl_hash + '\n')
            f.write(plc_version + '\n')
            f.write(pypi_name + '\n')

    def _get_installation_info():
        # Check if the versio to be installed matches the descritption saved during the last install.
        # If it matches, installation is skipped for efficiency
        # read the file
        info_file = root_folder / 'pyluxcore_installation.txt'

        if not os.path.exists(info_file):
            return 'None', 'None', 'None'
        
        with open(info_file, 'r') as f:
            old_wheel_hash = f.readline().strip()
            old_pyluxcore_version = f.readline().strip()
            old_pypi_wheel_name = f.readline().strip()

        return old_wheel_hash, old_pyluxcore_version, old_pypi_wheel_name
    
    def _clear_wheels():
        files = os.listdir(wheel_dl_folder)
        for file in files:
            os.remove(wheel_dl_folder / file)
    
    def _backup_wheels():
        files = os.listdir(wheel_dl_folder)
        for file in files:
            shutil.move(wheel_dl_folder / file, wheel_backup_folder / file)

    def _delete_backup_wheels():
        files = os.listdir(wheel_backup_folder)
        for file in files:
            os.remove(wheel_backup_folder / file)

    def _restore_backup_wheels():
        files = os.listdir(wheel_backup_folder)
        for file in files:
            shutil.move(wheel_backup_folder / file, wheel_dl_folder / file)

    def install_pyluxcore():
        # We cannot 'pip install' directly, as it would install pyluxcore system-wide
        # instead of in Blender environment
        # Blender has got its own logic for wheel installation, we'll rely on it

        # Step 0: Backup wheels
        _backup_wheels()

        # Step 1: Get PyPi information if needed
        if not blc_wheel_path and not _PYLUXCORE_VERSION:
            # Check if platform information is complete and valid
            architecture, machine, python_version_str = _get_platform_info()
            if architecture is None or machine is None or python_version_str is None:
                # In this case, just hope pyluxcore was previously installed and can be imported. Else error will be raised below so do nothing here at the moment.
                print("[BLC] WARNING: Platform information is incomplete. Installation of pyluxcore is not guaranteed to suceed!")
                return False
            # Try to get latest wheel information from PyPi
            pypi_wheel_name = _get_pypi_latest(architecture, machine, python_version_str)
            print("[BLC] PyPi latest version found:", pypi_wheel_name)
        else:
            pypi_wheel_name = 'None'

        # Step 2: get installation info for comaprison in following steps
        old_wheel_hash, old_pyluxcore_version, old_pypi_wheel_name = _get_installation_info()
        
        # Step 3: If BLC_WHEEL_PATH is specified, install that
        if blc_wheel_path:
            wheel_hash = base64.urlsafe_b64encode(hashlib.sha256(open(blc_wheel_path, 'rb').read()).digest()).decode('latin1').rstrip('=')
            if wheel_hash == old_wheel_hash:
                print("[BLC] skipping pyluxcore installation. Custom wheel matching hash already installed.")
                return True
            print('[BLC] Installing local version of pyluxcore')
            command = [
                        sys.executable,
                        '-m',
                        'pip',
                        'download',
                        blc_wheel_path,
                        '-d',
                        wheel_dl_folder
                    ]
            try:
                _execute_wheel_download(command)
                _delete_backup_wheels()
                _save_installation_info(wheel_hash, 'None', 'None')
                return True
            except:
                _clear_wheels()
                _restore_backup_wheels()
                return False
        
        # Step 4: If _PYLUXCORE_VERSION is specified, install that
        elif _PYLUXCORE_VERSION:
            if _PYLUXCORE_VERSION.strip() == old_pyluxcore_version.strip():
                print("[BLC] skipping pyluxcore installation. Specified version already installed.")
                return True
            print('[BLC] installing pyluxcore version:', _PYLUXCORE_VERSION)
            command = [
                        sys.executable,
                        '-m',
                        'pip',
                        'download',
                        f'pyluxcore=={_PYLUXCORE_VERSION}',
                        '-d',
                        wheel_dl_folder
                    ]
            try:
                _execute_wheel_download(command)
                _delete_backup_wheels()
                _save_installation_info('None', _PYLUXCORE_VERSION, 'None')
                return True
            except:
                _clear_wheels()
                _restore_backup_wheels()
                return False

        # Step 5: last option, install the latest version from PyPi
        else:
            if pypi_wheel_name == old_pypi_wheel_name:
                print("[BLC] Skipping pyluxcore installation. Latest version already installed.")
                return True
            print('[BLC] installing latest version of pyluxcore')
            command = [
                        sys.executable,
                        '-m',
                        'pip',
                        'download',
                        'pyluxcore',
                        '-d',
                        wheel_dl_folder
                    ]
            try:
                _execute_wheel_download(command)
                _delete_backup_wheels()
                _save_installation_info('None', 'None', pypi_wheel_name)
                return True
            except:
                _clear_wheels()
                _restore_backup_wheels()
                return False
            
    # We'll invoke install_pyluxcore at each init, execpt when BLC_WHEEL_PATH == "SKIP"
    # We rely on pip local cache for this call to be transparent, after the wheels
    # have been downloaded once, unless an update is required
    if blc_wheel_path == "SKIP":
        install_success = True
        print("[BLC] skipping pyluxcore installation...")
    else:
        install_success = install_pyluxcore()
    if not install_success:
        print('[BLC] WARNING: Download of pyluxcore not successful... Import will be attempted, but may be unsuccessful...')

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
    print('[BLC] USING LOCAL DEV VERSION OF BlendLuxCore')
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

import platform
import os
import sys
import subprocess
import shutil
import pathlib
import hashlib
import base64
from textwrap import dedent

import bpy
import addon_utils

# Check firts if Blender and OS versions are compatible
if bpy.app.version < (4, 2, 0):
    raise Exception("\n\nUnsupported Blender version. 4.2 or higher is required by BlendLuxCore.")

if platform.system() in {"Linux", "Darwin"}:
    # Required for downloads from the LuxCore Online Library
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

bl_info = {
    "name": "LuxCoreRender",
    "author": "Simon Wendsche (B.Y.O.B.), Michael Klemm (neo2068), Johannes Hinrichs (CodeHD), Howetuft, Odilkhan Yakubov (odil24), acasta69, u3dreal, Philstix",
    "version": (2, 10, 0),
    "blender": (4, 2, 0),
    "category": "Render",
    "description": "LuxCoreRender integration for Blender",
    "warning": "alpha.2",

    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}

version_string = f'{bl_info["version"][0]}.{bl_info["version"][1]}.{bl_info["version"][2]}'
if 'warning' in bl_info:
    version_string = version_string + f'-{bl_info["warning"]}'

PYLUXCORE_VERSION = '2.10.0a2' # specifies the version of pyluxcore that corresponds to this version of BlendLuxCore

# Check the location of this init file. The init file in the local dev folder returns only 'BlendLuxCore'
am_in_extension = __name__.startswith("bl_ext.")

# The environment variable BLC_DEV_PATH can be used to store a path
# to a local BlendLuxCore repository, which will then be imported
blc_dev_path = os.environ.get("BLC_DEV_PATH")

# The environment variable BLC_WHEEL_PATH can be used to store a path
# to a local pyluxcore wheel, which will then be installed
blc_wheel_path = os.environ.get("BLC_WHEEL_PATH")

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

    # As an alterniative for more user_friendly support:
    # Check for the presence of one(!) development wheel within the BlendLuxCore folder
    # This takes precedence over the BLC_WHEEL_PATH environment variable
    files, *_ = os.walk(wheel_dev_folder)
    files_filtered = [f for f in files[2] if f.startswith('pyluxcore') and f.endswith('.whl')]
    if len(files_filtered) > 1:
        print("[BLC] Warning: Content of 'pyluxcore_custom/' is not unique. Please delete all except one wheel file.")
    elif len(files_filtered) == 0:
        pass
    else:
        blc_wheel_path = wheel_dev_folder / files_filtered[0]

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

    def _save_installation_info(whl_hash='None', plc_version='None'):
        # Save information from the last installation.
        # Only one of the supplied arguments should be different from 'None'
        # to ensure that the type of installation is saved implicityly as well.
        info_file = root_folder / 'pyluxcore_installation_info.txt'
        header_text=dedent("""\
            # This file is used to store information about the pyluxcore installation.
            # It is used to determine whether a new installation is necessary at each startup.
            # Only one entry should be different from 'None', it indicates from which source
            # the installation was taken.
            #
            # The file is automatically generated and should not be edited manually.\n
        """)
        with open(info_file, 'w') as f:
            f.write(header_text)
            f.write(f'wheel-hash: {whl_hash}\n')
            f.write(f'pyluxcore-version: {plc_version}\n')

    def _get_installation_info():
        # Check if the versio to be installed matches the descritption saved during the last install.
        # If it matches, installation is skipped for efficiency
        # read the file
        info_file = root_folder / 'pyluxcore_installation_info.txt'

        if not os.path.exists(info_file):
            return 'None', 'None'
        
        with open(info_file, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith('#'): # comments
                    pass
                elif line.startswith('wheel-hash:'):
                    old_wheel_hash = line.split(':')[1].strip()
                elif line.startswith('pyluxcore-version:'):
                    old_pyluxcore_version = line.split(':')[1].strip()
                else:
                    pass

        return old_wheel_hash, old_pyluxcore_version
    
    def _clear_wheels():
        files = os.listdir(wheel_dl_folder)
        if len(files) == 0:
            return
        for file in files:
            os.remove(wheel_dl_folder / file)
    
    def _backup_wheels():
        files = os.listdir(wheel_dl_folder)
        if len(files) == 0:
            return
        for file in files:
            shutil.move(wheel_dl_folder / file, wheel_backup_folder / file)

    def _delete_backup_wheels():
        files = os.listdir(wheel_backup_folder)
        if len(files) == 0:
            return
        for file in files:
            os.remove(wheel_backup_folder / file)

    def _restore_backup_wheels():
        files = os.listdir(wheel_backup_folder)
        if len(files) == 0:
            return
        for file in files:
            shutil.move(wheel_backup_folder / file, wheel_dl_folder / file)

    def download_pyluxcore():
        # We cannot 'pip install' directly, as it would install pyluxcore system-wide
        # instead of in Blender environment
        # Blender has got its own logic for wheel installation, we'll rely on it

        # Step 0: Backup wheels from last successful installation
        _backup_wheels()

        # Step 1: get installation info for comaprison in following steps
        old_wheel_hash, old_pyluxcore_version = _get_installation_info()
        
        # Step 2: If BLC_WHEEL_PATH is specified, install that
        if blc_wheel_path:
            wheel_hash = base64.urlsafe_b64encode(hashlib.sha256(open(blc_wheel_path, 'rb').read()).digest()).decode('latin1').rstrip('=')
            if wheel_hash == old_wheel_hash:
                print("[BLC] skipping pyluxcore installation. Custom wheel matching hash already installed.")
                return 2
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
                _save_installation_info(wheel_hash, 'None')
                return 0
            except:
                _clear_wheels()
                _restore_backup_wheels()
                return 1
        
        # Step 3: If PYLUXCORE_VERSION is specified, install that
        elif PYLUXCORE_VERSION:
            if PYLUXCORE_VERSION.strip() == old_pyluxcore_version.strip():
                print("[BLC] skipping pyluxcore installation. Specified version already installed.")
                return 2
            print('[BLC] installing pyluxcore version:', PYLUXCORE_VERSION)
            command = [
                        sys.executable,
                        '-m',
                        'pip',
                        'download',
                        f'pyluxcore=={PYLUXCORE_VERSION}',
                        '-d',
                        wheel_dl_folder
                    ]
            try:
                _execute_wheel_download(command)
                _delete_backup_wheels()
                _save_installation_info('None', PYLUXCORE_VERSION)
                return 0
            except:
                _clear_wheels()
                _restore_backup_wheels()
                return 1

        # Step 4: Fallback, none of the above specified
        print("[BLC] ERROR: neither blc_wheel_path nor PYLUXCORE_VERSION specified in function download_pyluxcore()!")
        return 1
            
    # We'll invoke download_pyluxcore at each init
    # We rely on pip local cache for this call to be transparent,
    # after the wheels have been downloaded once, unless an update is required
    download_status = download_pyluxcore()
    if download_status == 0:
        # Ask Blender to do the install
        addon_utils.extensions_refresh(ensure_wheels=True)
    elif download_status == 1:
        # There was an error during download
        print('[BLC] WARNING: Download of pyluxcore not successful... Import will be attempted, but may be unsuccessful...')
    elif download_status == 2:
        # The version to be downloaded was already installed. Nothing to do.
        pass
    else:
        # Unknown error
        print('[BLC] WARNING: Unknown return code received from download_pyluxcore()... Import will be attempted, but may be unsuccessful...')

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
    print(f"BlendLuxCore {version_string} registered (with pyluxcore {pyluxcore.Version()})")

def unregister():
    engine.unregister()
    handlers.unregister()
    operators.unregister()
    properties.unregister()
    ui.unregister()
    nodes.unregister()

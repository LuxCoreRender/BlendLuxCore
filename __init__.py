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
    if bpy.app.version < (2, 82, 7):
        raise Exception("\n\nUnsupported Blender version. 2.82a or higher is required.")
    mac_version = tuple(map(int, platform.mac_ver()[0].split(".")))
    if mac_version < (10, 9, 0):
        raise Exception("\n\nUnsupported Mac OS version. 10.9 or higher is required.")

if platform.system() in {"Linux", "Darwin"}:
    # Required for downloads from the LuxCore Online Library
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

def get_wheel_filename(package_name, target_folder):
    # Get the current Python version and architecture
    python_version = sys.version_info
    python_version_str = f'cp{python_version.major}{python_version.minor}'
    architecture = None
    machine = None
    if platform.system() == "Darwin":
        architecture = 'macosx_'
        machine = platform.machine()
    elif platform.system() == "Linux":
        architecture = 'manylinux_'
        machine = 'x86_64'
    elif platform.system() == "Windows":
        architecture = 'win_' # including the underscore just to be safe this never pops up elsewhere in the future, 'win' is a pretty short string and common term
        machine = 'amd64'

    if architecture is None or machine is None:
        print('Warning: Platform could not be resolved in function get_wheel_filename(). Check is considered failed.')
        return None

    # Fetch package metadata from PyPI
    url = f'https://pypi.org/pypi/{package_name}/json'
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch metadata for package '{package_name}'")

    # Extract latest version of the package
    metadata = response.json()
    versions = metadata['releases']
    latest = list(versions.keys())[-1]

    # Iterate through all versions and look for appropriate wheel files
    for file in versions[latest]:
        fname = file['filename']
        if fname.endswith('.whl'):
            wheel_filename = fname
            if python_version_str in file['python_version'] and architecture in fname and machine in fname:
                return wheel_filename
    
    return None

def is_latest_wheel_present(package_name, target_folder):
    wheel_filename = get_wheel_filename(package_name, target_folder)
    if wheel_filename:
        wheel_path = os.path.join(target_folder, wheel_filename)
        if os.path.exists(wheel_path):
            return True
    # Finally, if wheel_filename is None or os.path.exists() returned False
    return False

def install_pyluxcore():
    # We cannot 'pip install' directly, as it would install pyluxcore system-wide
    # instead of in Blender environment
    # Blender has got its own logic for wheel installation, we'll rely on it

    root_folder = pathlib.Path(__file__).parent.resolve()
    wheel_folder =  root_folder / "wheels"

    # check if latest pyluxcore version has already been downloaded.
    # If yes, skip the download to save time
    pyluxcore_downloaded = is_latest_wheel_present('pyluxcore', wheel_folder)
    blc_wheel_path = os.environ.get("BLC_WHEEL_PATH")

    if pyluxcore_downloaded and not blc_wheel_path:
        print('Download of pyluxcore skipped, latest version was found on system')
        return

    print('Downloading pyluxcore')

    # Download wheel
    if not blc_wheel_path:
        command = [
            sys.executable,
            '-m',
            'pip',
            'download',
            'pyluxcore',
            '-d',
            wheel_folder
        ]
    else:
        command = [
            sys.executable,
            '-m',
            'pip',
            'download',
            blc_wheel_path,
            '-d',
            wheel_folder,
        ]

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
    wheel_statement = f"\nwheels = {wheels}\n"
    print(wheel_statement)

    with open(manifest_path, "r") as fp:
        manifest = list(fp)
    with open(manifest_path, "w") as fp:
        for line in manifest:
            if line.startswith("## WHEELS ##"):
                fp.write(wheel_statement)
            else:
                fp.write(line)

    # Ask Blender to do the install
    addon_utils.extensions_refresh(ensure_wheels=True)


# We'll invoke install_pyluxcore at each init
# We rely on pip local cache for this call to be transparent, after the wheels
# have been downloaded once, unless an update is required
install_pyluxcore()

try:
    import pyluxcore
except ImportError as error:
    msg = "\n\nCould not import pyluxcore."
    # Raise from None to suppress the unhelpful
    # "during handling of the above exception, ..."
    raise RuntimeError(msg + "\n\nImportError: %s" % error) from None

bl_info = {
    "name": "LuxCoreRender",
    "author": "Simon Wendsche (B.Y.O.B.), Michael Klemm (neo2068), Odilkhan Yakubov (odil24), acasta69, u3dreal, Philstix",
    "version": (2, 9),
    "blender": (4, 2, 0),
    "category": "Render",
    "description": "LuxCoreRender integration for Blender",
    "warning": "alpha3",

    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}
version_string = f'{bl_info["version"][0]}.{bl_info["version"][1]}{bl_info["warning"]}'

from . import properties, engine, handlers, operators, ui, nodes

def register():
    engine.register()
    handlers.register()
    operators.register()
    properties.register()
    ui.register()
    nodes.register()

    from .utils.log import LuxCoreLog
    pyluxcore.Init(LuxCoreLog.add)
    print(f"BlendLuxCore (wheels) {version_string} registered (with pyluxcore {pyluxcore.Version()})")

def unregister():
    engine.unregister()
    handlers.unregister()
    operators.unregister()
    properties.unregister()
    ui.unregister()
    nodes.unregister()

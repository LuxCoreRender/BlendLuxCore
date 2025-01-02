print("here")
import tempfile
import platform
import os
import sys
import subprocess
from shutil import which
import pathlib

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


def install_pyluxcore():
    # We cannot 'pip install' directly, as it would install pyluxcore system-wide
    # instead of in Blender environment
    # Blender has got its own logic for wheel installation, we'll rely on it

    # Download wheel
    root_folder = pathlib.Path(__file__).parent.resolve()
    wheel_folder =  root_folder / "wheels"
    command = [
        sys.executable,
        '-m',
        'pip',
        'download',
        'pyluxcore',
        '-d',
        wheel_folder
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    output = stdout.decode()
    error_output = stderr.decode()
    if output:
        print("Output:\n", output)
    if error_output:
        print("Errors:\n", error_output)

    if process.returncode != 0:
        raise RuntimeError(f'Failed to download LuxCore with return code {result.returncode}.') from None

    # Setup manifest with wheel list
    manifest_path = root_folder / "blender_manifest.toml"
    files, *_ = os.walk(wheel_folder)
    wheels = [os.path.join(".", "wheels", f) for f in files[2]]
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
    "warning": "beta2",

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
    print(f"BlendLuxCore {version_string} registered (with pyluxcore {pyluxcore.Version()})")

def unregister():
    engine.unregister()
    handlers.unregister()
    operators.unregister()
    properties.unregister()
    ui.unregister()
    nodes.unregister()

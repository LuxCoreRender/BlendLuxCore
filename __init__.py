import platform
import os
import sys
import pathlib
import tomllib

_needs_reload = "bpy" in locals()

import bpy
import addon_utils

from . import luxloader

if _needs_reload:
    import importlib
    luxloader = importlib.reload(luxloader)

# Check first if Blender and OS versions are compatible
if bpy.app.version < (4, 2, 0):
    raise RuntimeError(
        "\n\nUnsupported Blender version. "
        "4.2 or higher is required by BlendLuxCore."
    )

if platform.system() in {"Linux", "Darwin"}:
    # Required for downloads from the LuxCore Online Library
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Load version information from blender_manifest.toml.
# Replaced the old "bl_info" dictionary.
manifest_path = pathlib.Path(__file__).parent.resolve() / 'blender_manifest.toml'
with open(manifest_path, "rb") as f:
    manifest_data = tomllib.load(f)
version_string = manifest_data['version']

luxloader.ensure_pyluxcore()

try:
    import pyluxcore
except ImportError as error:
    msg = f"\n\nCould not import pyluxcore. \n\nImportError: {error}"
    # Raise from None to suppress the unhelpful
    # "during handling of the above exception, ..."
    raise RuntimeError(msg) from None

if luxloader.BLC_OFFLINE_INSTALL:
    # remove the install_offline_folder because we want a normal startup next time
    luxloader.delete_install_offline()

if luxloader.BLC_DEV_PATH and luxloader.AM_IN_EXTENSION:
    # TODO This code is problematic:
    # - BlendLuxCore imports itself
    # - engine, handlers etc. are not guaranteed to be set, which can make `register`
    #   raise
    # - it defines `unregister`, making below declaration redefine
    print('[BLC] USING LOCAL DEV VERSION OF BlendLuxCore')
    sys.path.insert(0, luxloader.BLC_DEV_PATH)
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
    print(
        f"BlendLuxCore {version_string} registered "
        f"(with pyluxcore {pyluxcore.Version()})"
    )

def unregister():
    engine.unregister()
    handlers.unregister()
    operators.unregister()
    properties.unregister()
    ui.unregister()
    nodes.unregister()

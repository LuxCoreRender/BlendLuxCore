# Import standard modules
import platform
import os
import sys
import pathlib
from importlib.metadata import version

if platform.system() in {"Linux", "Darwin"}:
    # Required for downloads from the LuxCore Online Library
    import certifi

    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

bl_info = {
    "name": "LuxCoreRender",
    "author": "Simon Wendsche (B.Y.O.B.), Michael Klemm (neo2068), Johannes Hinrichs (CodeHD), Howetuft, Odilkhan Yakubov (odil24), acasta69, u3dreal, Philstix",
    "version": (2, 10, 1),
    "blender": (4, 2, 0),
    "category": "Render",
    "description": "LuxCoreRender integration for Blender",
    #"warning": "rc.1",

# Import Blender packages
import bpy
import addon_utils
import nodeitems_utils

# Check if Blender and OS versions are compatible
if bpy.app.version < (4, 2, 0):
    raise RuntimeError(
        "\n\nUnsupported Blender version. "
        "4.2 or higher is required by BlendLuxCore."
    )

PYLUXCORE_VERSION = '2.10.1' # specifies the version of pyluxcore that corresponds to this version of BlendLuxCore

# Take care of PyLuxCore, as other modules may want to import it
from . import luxloader

if _needs_reload:
    import importlib

    luxloader = importlib.reload(luxloader)

luxloader.ensure_pyluxcore()

# Import pyluxcore
try:
    import pyluxcore
except ImportError as error:
    msg = f"\n\nCould not import pyluxcore. \n\nImportError: {error}"
    # Raise from None to suppress the unhelpful
    # "during handling of the above exception, ..."
    raise RuntimeError(msg) from error


# Import other modules
from . import utils, properties, export, nodes, operators, engine, handlers, ui

if _needs_reload:
    import importlib

    utils = importlib.reload(utils)
    properties = importlib.reload(properties)
    export = importlib.reload(export)
    nodes = importlib.reload(nodes)
    operators = importlib.reload(operators)
    handlers = importlib.reload(handlers)
    engine = importlib.reload(engine)
    ui = importlib.reload(ui)


# Handle registering and unregistering
# Warning: submodule order matters (for reloading, in particular)
submodules = (properties, nodes, operators, handlers, engine, ui)

def register():
    utils.register_module("Main", [], submodules)

    pyluxcore.Init(utils.log.LuxCoreLog.add)
    print(
        f"BlendLuxCore {utils.get_version_string()} registered "
        f"(with pyluxcore {version('pyluxcore')})"
    )


def unregister():
    utils.unregister_module("Main", [], submodules)

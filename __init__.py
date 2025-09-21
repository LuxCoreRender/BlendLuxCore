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

# Support reloading
# https://developer.blender.org/docs/handbook/extensions/addon_dev_setup/#reloading-scripts
_needs_reload = "bpy" in locals()

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
    raise RuntimeError(msg) from None


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

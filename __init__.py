import platform
import os
import sys
import pathlib

if platform.system() in {"Linux", "Darwin"}:
    # Required for downloads from the LuxCore Online Library
    import certifi

    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Support reloading
# https://developer.blender.org/docs/handbook/extensions/addon_dev_setup/#reloading-scripts
_needs_reload = "bpy" in locals()

import bpy
import addon_utils

# Before all, check if Blender and OS versions are compatible
if bpy.app.version < (4, 2, 0):
    raise RuntimeError(
        "\n\nUnsupported Blender version. "
        "4.2 or higher is required by BlendLuxCore."
    )

# Then, take care of ensuring PyLuxCore, as other modules may want to import it
from . import luxloader

if _needs_reload:
    import importlib

    luxloader = importlib.reload(luxloader)

luxloader.ensure_pyluxcore()

try:
    import pyluxcore
except ImportError as error:
    msg = f"\n\nCould not import pyluxcore. \n\nImportError: {error}"
    # Raise from None to suppress the unhelpful
    # "during handling of the above exception, ..."
    raise RuntimeError(msg) from None
if _needs_reload:
    import importlib

    pyluxcore = importlib.reload(pyluxcore)

# Then import other modules (and deal with reloading)
from . import properties, engine, handlers, operators, ui, nodes, utils
from .utils.log import LuxCoreLog

if _needs_reload:
    import importlib

    properties = importlib.reload(properties)
    engine = importlib.reload(engine)
    handlers = importlib.reload(handlers)
    operators = importlib.reload(operators)
    ui = importlib.reload(ui)
    nodes = importlib.reload(nodes)
    utils = importlib.reload(utils)


def register():
    engine.register()
    handlers.register()
    operators.register()
    properties.register()
    ui.register()
    nodes.register()

    pyluxcore.Init(LuxCoreLog.add)
    print(
        f"BlendLuxCore {utils.get_version_string()} registered "
        f"(with pyluxcore {pyluxcore.Version()})"
    )


def unregister():
    engine.unregister()
    handlers.unregister()
    operators.unregister()
    properties.unregister()
    ui.unregister()
    nodes.unregister()

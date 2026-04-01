# Import standard modules
import platform
import os
import sys
import pathlib
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # backport: pip install tomli
from importlib.metadata import version

_needs_reload = "bpy" in locals()

from . import luxloader

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

# Check the location of this init file. The init file in the local dev folder returns only 'BlendLuxCore'
am_in_extension = __package__.startswith("bl_ext.")

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

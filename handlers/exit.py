_needs_reload = "bpy" in locals()
import bpy

from .. import export, draw, pyluxcore
from ..export.image import ImageExporter
from ..draw.viewport import TempfileManager
import pyluxcore

if _needs_reload:
    import importlib
    modules = (
        export,
        draw,
        pyluxcore,
    )
    for module in modules:
        importlib.reload(module)


def handler():
    ImageExporter.cleanup()
    TempfileManager.cleanup()

    # Workaround for a bug in LuxCore:
    # We have to uninstall the log handler to prevent a crash.
    # https://github.com/LuxCoreRender/LuxCore/issues/29
    pyluxcore.SetLogHandler(None)

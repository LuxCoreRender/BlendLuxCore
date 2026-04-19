_needs_reload = "bpy" in locals()

import bpy
from . import final
from . import viewport
from . import utils

if _needs_reload:
    import importlib
    # Reload submodules when bpy has been cached (developer reload)
    importlib.reload(final)
    importlib.reload(viewport)
    importlib.reload(utils)

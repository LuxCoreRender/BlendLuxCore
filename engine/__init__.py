_needs_reload = "bpy" in locals()

import bpy

from .. import utils
from . import base

if _needs_reload:
    import importlib
    importlib.reload(base)

classes = (base.LuxCoreRenderEngine,)

def register():
    utils.register_module("Engine", classes)

def unregister():
    utils.unregister_module("Engine", classes)

_needs_reload = "bpy" in locals()

import bpy


from bpy.utils import register_class, unregister_class
from . import base

if _needs_reload:
    import importlib
    importlib.reload(base)

def register():
    register_class(base.LuxCoreRenderEngine)

def unregister():
    unregister_class(base.LuxCoreRenderEngine)

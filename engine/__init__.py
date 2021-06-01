from bpy.utils import register_class, unregister_class
from . import base

def register():
    register_class(base.LuxCoreRenderEngine)

def unregister():
    unregister_class(base.LuxCoreRenderEngine)

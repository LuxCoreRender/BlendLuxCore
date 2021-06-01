from bpy.utils import register_class, unregister_class
from . import assetmenu, panel

classes = (
    assetmenu.OBJECT_MT_LOL_asset_menu,
    panel.VIEW3D_PT_LUXCORE_ONLINE_LIBRARY,
    panel.VIEW3D_PT_LUXCORE_ONLINE_LIBRARY_DOWNLOADS,
    panel.VIEW3D_PT_LUXCORE_ONLINE_LIBRARY_LOCAL,
    panel.VIEW3D_PT_LUXCORE_ONLINE_LIBRARY_SCAN_RESULT,
)

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in classes:
        unregister_class(cls)

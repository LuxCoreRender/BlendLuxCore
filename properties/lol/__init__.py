from bpy.utils import register_class, unregister_class
from . import LuxCoreOLScene

classes = (
    LuxCoreOLScene.LuxCoreOnlineLibraryAssetBar,
    LuxCoreOLScene.LuxCoreOnlineLibraryUI,
    LuxCoreOLScene.LuxCoreOnlineLibraryModel,
    LuxCoreOLScene.LuxCoreOnlineLibraryMaterial,
    LuxCoreOLScene.LuxCoreOnlineLibraryScene,
    LuxCoreOLScene.LuxCoreOnlineLibraryAsset,
    LuxCoreOLScene.LuxCoreOnlineLibraryUpload,
    LuxCoreOLScene.LuxCoreOnlineLibrary,
)

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in classes:
        unregister_class(cls)

from ... import utils
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
    utils.register_module("Properties.Lol", classes)

def unregister():
    utils.unregister_module("Properties.Lol", classes)

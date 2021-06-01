from bpy.utils import register_class, unregister_class
from . import add_local, assetbar, update_ToC

classes = (
    add_local.LOLAddLocalOperator,
    add_local.LOLScanLocalOperator,
    assetbar.LOLAssetBarOperator,
    assetbar.LOLAssetKillDownloadOperator,
    update_ToC.LOLUpdateTOC,
)

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in classes:
        unregister_class(cls)

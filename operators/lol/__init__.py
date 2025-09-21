from ... import utils
from . import add_local, assetbar, update_ToC

classes = (
    add_local.LOLAddLocalOperator,
    add_local.LOLScanLocalOperator,
    assetbar.LOLAssetBarOperator,
    assetbar.LOLAssetKillDownloadOperator,
    update_ToC.LOLUpdateTOC,
)

def register():
    utils.register_module("Operators.Lol", classes)

def unregister():
    utils.unregister_module("Operators.Lol", classes)

import nodeitems_utils
from .tree import luxcore_node_categories_material

# Import all material nodes just so they get registered
from .carpaint import LuxCoreNodeMatCarpaint
from .cloth import LuxCoreNodeMatCloth
from .emission import LuxCoreNodeMatEmission
from .frontbackopacity import LuxCoreNodeMatFrontBackOpacity
from .glass import LuxCoreNodeMatGlass
from .glossytranslucent import LuxCoreNodeMatGlossyTranslucent
from .glossy2 import LuxCoreNodeMatGlossy2
from .glossycoating import LuxCoreNodeMatGlossyCoating
from .matte import LuxCoreNodeMatMatte
from .mattetranslucent import LuxCoreNodeMatMatteTranslucent
from .metal import LuxCoreNodeMatMetal
from .mirror import LuxCoreNodeMatMirror
from .mix import LuxCoreNodeMatMix
from .velvet import LuxCoreNodeMatVelvet
from .null import LuxCoreNodeMatNull
from .output import LuxCoreNodeMatOutput


def register():
    nodeitems_utils.register_node_categories("LUXCORE_MATERIAL_TREE", luxcore_node_categories_material)


def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_MATERIAL_TREE")

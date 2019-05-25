import nodeitems_utils
from .tree import luxcore_node_categories_volume

# Import all volume nodes just so they get registered
# TODO 2.8 remove
from .output import LuxCoreNodeVolOutput
from .clear import LuxCoreNodeVolClear
from .homogeneous import LuxCoreNodeVolHomogeneous
from .heterogeneous import LuxCoreNodeVolHeterogeneous


def register():
    nodeitems_utils.register_node_categories("LUXCORE_VOLUME_TREE", luxcore_node_categories_volume)


def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_VOLUME_TREE")

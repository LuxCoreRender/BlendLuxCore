import nodeitems_utils
from .tree import luxcore_node_categories_volume

def register():
    nodeitems_utils.register_node_categories("LUXCORE_VOLUME_TREE", luxcore_node_categories_volume)


def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_VOLUME_TREE")

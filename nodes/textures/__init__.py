import nodeitems_utils
from .tree import luxcore_node_categories_texture

def register():
    nodeitems_utils.register_node_categories("LUXCORE_TEXTURE_TREE", luxcore_node_categories_texture)


def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_TEXTURE_TREE")

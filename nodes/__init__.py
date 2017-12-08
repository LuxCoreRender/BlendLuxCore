import bpy
from bpy.types import Node


class LuxCoreNode(Node):
    bl_label = ""

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname in ['luxcore_material_nodes']
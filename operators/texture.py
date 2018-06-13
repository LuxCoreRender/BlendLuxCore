import bpy
from .utils import init_tex_node_tree


class LUXCORE_OT_tex_nodetree_new(bpy.types.Operator):
    bl_idname = "luxcore.tex_nodetree_new"
    bl_label = "New"
    bl_description = "Create a texture node tree"
    bl_options = {"UNDO"}

    def execute(self, context):
        name = "Texture Node Tree"
        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_texture_nodes")
        init_tex_node_tree(node_tree)

        return {"FINISHED"}
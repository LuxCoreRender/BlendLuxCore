import bpy
from bpy.types import PropertyGroup
from bpy.props import PointerProperty, FloatProperty, BoolProperty
from ..utils import node as utils_node
from ..operators.material import show_nodetree


class LuxCoreMaterialPreviewProps(PropertyGroup):
    def update_preview(self, context):
        material = self.id_data
        # A trick to force a material preview refresh (update_tag() does not work)
        material.preview_render_type = material.preview_render_type

    zoom: FloatProperty(name="Zoom", default=1, min=1, soft_max=3, max=10,
                         description="Zoom of the preview camera",
                         update=update_preview)


class LuxCoreMaterialProps(PropertyGroup):
    def update_auto_vp_color(self, context):
        if self.auto_vp_color:
            utils_node.update_opengl_materials(None, context)

    auto_vp_color: BoolProperty(name="Automatic Viewport Color", default=True,
                                 update=update_auto_vp_color,
                                 description="Automatically choose a viewport color "
                                             "from the first nodes in the node tree")
    node_tree: PointerProperty(name="Node Tree", type=bpy.types.NodeTree)
    preview: PointerProperty(type=LuxCoreMaterialPreviewProps)

    def update_use_cycles_nodes(self, context):
        mat = self.id_data
        node_tree = mat.node_tree if mat.luxcore.use_cycles_nodes else mat.luxcore.node_tree
        if node_tree:
            show_nodetree(context, node_tree)

    use_cycles_nodes: BoolProperty(name="Use Cycles Nodes", default=False, update=update_use_cycles_nodes,
                                   description="Use the Cycles nodes of this material instead of the LuxCore node tree "
                                               "(WARNING: This option is not fully implemented yet, only very few nodes work)")

    @classmethod
    def register(cls):        
        bpy.types.Material.luxcore = PointerProperty(
            name="LuxCore Material Settings",
            description="LuxCore material settings",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Material.luxcore

import bpy
from bpy.types import PropertyGroup
from bpy.props import PointerProperty, FloatProperty, BoolProperty
from ..utils import node as utils_node


def init():
    bpy.types.Material.luxcore = PointerProperty(type=LuxCoreMaterialProps)


class LuxCoreMaterialPreviewProps(PropertyGroup):
    def update_preview(self, context):
        material = self.id_data
        # A trick to force a material preview refresh (update_tag() does not work)
        material.preview_render_type = material.preview_render_type

    size = FloatProperty(name="Sphere Size (m)", default=0.1, min=0.01, soft_max=1,
                         description="Diameter of the preview sphere in meters\n"
                                     "(one checker tile has a size of 10cm)",
                         update=update_preview)

    zoom = FloatProperty(name="Zoom", default=1, min=1, soft_max=3, max=10,
                         description="Zoom of the preview camera",
                         update=update_preview)


class LuxCoreMaterialProps(PropertyGroup):
    def update_auto_vp_color(self, context):
        if self.auto_vp_color:
            utils_node.update_opengl_materials(None, context)

    auto_vp_color = BoolProperty(name="Automatic Viewport Color", default=True,
                                 update=update_auto_vp_color,
                                 description="Automatically choose a viewport color "
                                             "from the first nodes in the node tree")
    node_tree = PointerProperty(name="Node Tree", type=bpy.types.NodeTree)
    preview = PointerProperty(type=LuxCoreMaterialPreviewProps)

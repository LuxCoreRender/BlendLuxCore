import bpy
from bpy.types import PropertyGroup
from bpy.props import PointerProperty, FloatProperty


def init():
    bpy.types.Material.luxcore = PointerProperty(type=LuxCoreMaterialProps)


class LuxCoreMaterialPreviewProps(PropertyGroup):
    def update_preview(self, context):
        material = self.id_data
        # A trick to force a material preview refresh (update_tag() does not work)
        material.preview_render_type = material.preview_render_type

    size = FloatProperty(name="Sphere Size (m)", default=0.1, min=0.01, soft_max=1,
                         description="Diameter of the preview sphere in meters"
                                     "(one checker tile has a size of 10cm)",
                         update=update_preview)

    zoom = FloatProperty(name="Zoom", default=1, min=1, soft_max=3, max=10,
                         description="Zoom of the preview camera",
                         update=update_preview)


class LuxCoreMaterialProps(PropertyGroup):
    node_tree = PointerProperty(name="Node Tree", type=bpy.types.NodeTree)
    preview = PointerProperty(type=LuxCoreMaterialPreviewProps)

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from ..base import LuxCoreNodeTexture

from ... import utils
from ...utils import node as utils_node


class LuxCoreNodeTexBlenderBlend(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Blender Blend"
    bl_width_default = 200    

    progression_items = [
        ("linear", "Linear", "linear"),
        ("quadratic", "Quadratic", "quadratic"),
        ("easing", "Easing", "easing"),
        ("diagonal", "Diagonal", "diagonal"),
        ("spherical", "Spherical", "spherical"),
        ("halo", "Quadratic Sphere", "quadratic sphere"),
        ("radial", "Radial", "radial"),
    ]

    direction_items = [
        ("horizontal", "Horizontal", "Direction: -x to x"),
        ("vertical", "Vertical", "Direction: -y to y")
    ]

    progression_type: EnumProperty(update=utils_node.force_viewport_update, name="Progression", description="progression", items=progression_items, default="linear")
    direction: EnumProperty(update=utils_node.force_viewport_update, name="Direction", items=direction_items, default="horizontal")

    bright: FloatProperty(update=utils_node.force_viewport_update, name="Brightness", default=1.0, min=0)
    contrast: FloatProperty(update=utils_node.force_viewport_update, name="Contrast", default=1.0, min=0)

    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "direction", expand=True)
        layout.prop(self, "progression_type")

        col = layout.column(align=True)
        col.prop(self, "bright")
        col.prop(self, "contrast")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, depsgraph, props)
       
        definitions = {
            "type": "blender_blend",
            "progressiontype": self.progression_type,
            "direction": self.direction,
            "bright": self.bright,
            "contrast": self.contrast,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }
        
        return self.create_props(props, definitions, luxcore_name)

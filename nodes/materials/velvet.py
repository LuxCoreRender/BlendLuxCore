import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from ..base import LuxCoreNodeMaterial
from ...utils import node as utils_node


class LuxCoreNodeMatVelvet(LuxCoreNodeMaterial, bpy.types.Node):
    bl_label = "Velvet Material"
    bl_width_default = 160

    def update_advanced(self, context):
        sockets = ["p1", "p2", "p3"]

        for socket in sockets:
            id = self.inputs.find(socket)
            self.inputs[id].enabled = self.advanced

        utils_node.force_viewport_update(self, context)

    advanced: BoolProperty(name="Advanced Options", description="Advanced Velvet Parameters", default=False, update=update_advanced)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Diffuse Color", (1, 1, 1))
        self.add_input("LuxCoreSocketFloat0to1", "Thickness", 0.1)
        self.add_input("LuxCoreSocketFloatUnbounded", "p1", 2)
        self.add_input("LuxCoreSocketFloatUnbounded", "p2", 10)
        self.add_input("LuxCoreSocketFloatUnbounded", "p3", 2)
        self.inputs["p1"].enabled = False
        self.inputs["p2"].enabled = False
        self.inputs["p3"].enabled = False
                
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        layout.prop(self, "advanced", toggle=True)

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "velvet",
            "kd": self.inputs["Diffuse Color"].export(exporter, depsgraph, props),
            "thickness": self.inputs["Thickness"].export(exporter, depsgraph, props),
        }

        if self.advanced:
            definitions.update({
                "p1": self.inputs["p1"].export(exporter, depsgraph, props),
                "p2": self.inputs["p2"].export(exporter, depsgraph, props),
                "p3": self.inputs["p3"].export(exporter, depsgraph, props),
            })

        self.export_common_inputs(exporter, depsgraph, props, definitions)
        return self.create_props(props, definitions, luxcore_name)

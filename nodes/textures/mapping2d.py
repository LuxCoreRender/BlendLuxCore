import bpy
import math
from bpy.props import FloatProperty, BoolProperty, StringProperty, IntProperty
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexMapping2D(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "2D Mapping"
    bl_width_default = 160

    def update_uvmap(self, context):
        self.uvindex = context.object.data.uv_layers.find(self.uvmap)
        utils_node.force_viewport_update(self, context)

    def update_uniform_scale(self, context):
        self["uscale"] = self.uniform_scale
        self["vscale"] = self.uniform_scale
        utils_node.force_viewport_update(self, context)

    # TODO descriptions
    use_uniform_scale: BoolProperty(update=utils_node.force_viewport_update, name="Uniform Scale", default=True)
    uniform_scale: FloatProperty(name="UV Scale", default=1, update=update_uniform_scale)
    uscale: FloatProperty(update=utils_node.force_viewport_update, name="U", default=1)
    vscale: FloatProperty(update=utils_node.force_viewport_update, name="V", default=1)
    rotation: FloatProperty(update=utils_node.force_viewport_update, name="Rotation", default=0, min=(-math.pi * 2),
                             max=(math.pi * 2), subtype="ANGLE", unit="ROTATION")
    udelta: FloatProperty(update=utils_node.force_viewport_update, name="U", default=0)
    vdelta: FloatProperty(update=utils_node.force_viewport_update, name="V", default=0)
    center_map: BoolProperty(update=utils_node.force_viewport_update, name="Center Map", default=False)
    uvmap: StringProperty(update=update_uvmap, name="UV Map")
    uvindex: IntProperty(name="UV Index", default=0)

    def init(self, context):
        # Instead of creating a new mapping, the user can also
        # manipulate an existing mapping
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping (optional)")

        self.outputs.new("LuxCoreSocketMapping2D", "2D Mapping")

    def draw_buttons(self, context, layout):
        # Info about UV mapping so the user can react if no UV map etc.
        utils_node.draw_uv_info(context, layout)

        if not self.inputs["2D Mapping (optional)"].is_linked:
            layout.prop_search(self, "uvmap", context.object.data, "uv_layers", text="UV Map", icon='GROUP_UVS')
        layout.prop(self, "center_map")
        layout.prop(self, "use_uniform_scale")

        if self.use_uniform_scale:
            layout.prop(self, "uniform_scale")
        else:
            row = layout.row(align=True)
            row.prop(self, "uscale")
            row.prop(self, "vscale")

        layout.prop(self, "rotation")

        layout.label(text="Offset:")
        row = layout.row(align=True)
        row.prop(self, "udelta")
        row.prop(self, "vdelta")

    def export(self, exporter, despgraph, props, luxcore_name=None, output_socket=None):
        input_socket = self.inputs["2D Mapping (optional)"]
        if utils_node.get_link(input_socket):
            uvindex, input_uvscale, input_rotation, input_uvdelta = input_socket.export(exporter, despgraph, props)
        else:
            uvindex = self.uvindex
            input_uvscale = [1, -1]
            input_rotation = 0
            input_uvdelta = [0, 0]

        # Scale
        if self.use_uniform_scale:
            uvscale = [self.uniform_scale, self.uniform_scale]
        else:
            uvscale = [self.uscale, self.vscale]
        output_uvscale = [a * b for a, b in zip(input_uvscale, uvscale)]

        # Rotation
        rotation = math.degrees(self.rotation)
        output_rotation = input_rotation + rotation

        # Translation
        if self.center_map:
            uvdelta = [self.udelta + 0.5 * (1 - uvscale[0]),
                       self.vdelta * -1 + 1 - (0.5 * (1 - uvscale[1]))]
        else:
            uvdelta = [self.udelta,
                       self.vdelta + 1]
        output_uvdelta = [a + b for a, b in zip(input_uvdelta, uvdelta)]

        return uvindex, output_uvscale, output_rotation, output_uvdelta

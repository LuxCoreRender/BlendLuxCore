import bpy
from bpy.props import FloatProperty
from ..base import LuxCoreNodeTexture, LuxCoreNodeMaterial
from ...utils import node as utils_node
from ... import icons


SAMPLING_DISTANCE_DESC = (
    "Distance to use when picking two points on the surface for bump gradient calculation.\n"
    "Use smaller values if procedural bump textures with very fine details don't show a bump effect.\n"
    "Does not affect bump sampling of image textures"
)


class LuxCoreNodeTexBump(LuxCoreNodeTexture, bpy.types.Node):
    bl_label = "Bump"
    bl_width_default = 200

    # Note: exported in the export_common_inputs() method of material nodes
    sampling_distance: FloatProperty(name="Sampling Distance",
                                     default=0.001, min=0.000001, soft_max=0.001, step=0.00001,
                                     subtype="DISTANCE",
                                     description=SAMPLING_DISTANCE_DESC,
                                     update=utils_node.force_viewport_update)

    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Value", 0.0)
        self.add_input("LuxCoreSocketBumpHeight", "Bump Height", 0.001)

        self.outputs.new("LuxCoreSocketBump", "Bump")

    def draw_buttons(self, context, layout):
        utils_node.draw_uv_info(context, layout)

        show_triplanar_warning = False
        value_node = utils_node.get_linked_node(self.inputs["Value"])
        if value_node and value_node.bl_idname == "LuxCoreNodeTexTriplanar":
            show_triplanar_warning = True
        else:
            height_node = utils_node.get_linked_node(self.inputs["Bump Height"])
            if height_node and height_node.bl_idname == "LuxCoreNodeTexTriplanar":
                show_triplanar_warning = True

        if show_triplanar_warning:
            layout.label(text="Use triplanar bump node instead!", icon=icons.WARNING)

        col = layout.column()
        output = self.outputs["Bump"]
        col.active = output.is_linked and isinstance(output.links[0].to_node, LuxCoreNodeMaterial)
        col.prop(self, "sampling_distance")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "scale",
            "texture1": self.inputs["Value"].export(exporter, depsgraph, props),
            "texture2": self.inputs["Bump Height"].export(exporter, depsgraph, props),
        }
        return self.create_props(props, definitions, luxcore_name)

import bpy
from bpy.props import BoolProperty
from ..output import LuxCoreNodeOutput, update_active
from ... import utils


class LuxCoreNodeTexOutput(bpy.types.Node, LuxCoreNodeOutput):
    """
    Texture output node.
    This is where the export starts (if the output is active).
    """
    bl_label = "Texture Output"
    bl_width_default = 160

    active: BoolProperty(name="Active", default=True, update=update_active)

    def init(self, context):
        self.inputs.new("LuxCoreSocketColor", "Color")
        self.inputs["Color"].needs_link = True
        super().init(context)

    def export(self, exporter, depsgraph, props, luxcore_name):
        # Invalidate node cache
        # TODO have one global properties object so this is no longer necessary
        exporter.node_cache.clear()

        color = self.inputs["Color"].export(exporter, depsgraph, props, luxcore_name)

        if not self.inputs["Color"].is_linked:
            # We need a helper texture
            helper_prefix = "scene.textures." + luxcore_name + "."
            helper_defs = {
                "type": "constfloat3",
                "value": color,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))

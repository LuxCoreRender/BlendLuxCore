import bpy
from bpy.props import BoolProperty
from ..output import LuxCoreNodeOutput, update_active
from .. import utils


class LuxCoreNodeVolOutput(LuxCoreNodeOutput):
    """
    Volume output node.
    This is where the export starts (if the output is active).
    """
    bl_label = "Volume Output"
    bl_width_default = 160

    active = BoolProperty(name="Active", default=True, update=update_active)

    def init(self, context):
        self.inputs.new("LuxCoreSocketVolume", "Volume")
        super().init(context)

    def export(self, exporter, props, luxcore_name):
        # Invalidate node cache
        # TODO have one global properties object so this is no longer necessary
        exporter.node_cache.clear()

        if self.inputs["Volume"].is_linked:
            self.inputs["Volume"].export(exporter, props, luxcore_name)
        else:
            # We need a fallback (black volume)
            msg = 'Node "%s" in tree "%s": No volume attached' % (self.name, self.id_data.name)
            exporter.scene.luxcore.errorlog.add_warning(msg)

            helper_prefix = "scene.volumes." + luxcore_name + "."
            helper_defs = {
                "type": "clear",
                "absorption": [100, 100, 100],
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))

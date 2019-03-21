import bpy
from bpy.props import BoolProperty
from ..output import LuxCoreNodeOutput, update_active
from .. import utils
from ...bin import pyluxcore


class LuxCoreNodeVolOutput(LuxCoreNodeOutput):
    """
    Volume output node.
    This is where the export starts (if the output is active).
    """
    bl_label = "Volume Output"
    bl_width_default = 160

    active = BoolProperty(name="Active", default=True, update=update_active)
    use_photongi = BoolProperty(name="Use PhotonGI Cache", default=True,
                                description="Store PhotonGI entries in this volume. This only affects "
                                            "homogeneous and heterogeneous volumes, entries are never "
                                            "stored on clear volumes. You might want to disable this "
                                            "for volumes that take up a lot of space while having low "
                                            "scattering, like a fog volume in a large open scene")

    def init(self, context):
        self.inputs.new("LuxCoreSocketVolume", "Volume")
        super().init(context)

    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)

        # PhotonGI currently only works with Path engine
        if (context.scene.luxcore.config.photongi.enabled
                and context.scene.luxcore.config.engine == "PATH"):
            # PhotonGI only affects homogeneous and heterogeneous volumes, make the setting inactive for others
            linked_node = self.inputs["Volume"].links[0].from_node if self.inputs["Volume"].is_linked else False
            row = layout.row()
            row.active = linked_node and linked_node.bl_idname in {"LuxCoreNodeVolHomogeneous",
                                                                   "LuxCoreNodeVolHeterogeneous"}
            row.prop(self, "use_photongi")

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

        prefix = "scene.volumes." + luxcore_name + "."
        props.Set(pyluxcore.Property(prefix + "photongi.enable", self.use_photongi))

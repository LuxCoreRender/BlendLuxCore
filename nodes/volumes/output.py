import bpy
from bpy.props import BoolProperty, IntProperty
from ..output import LuxCoreNodeOutput, update_active
from ..materials.output import MATERIAL_ID_DESC
from ... import utils
import pyluxcore
from ...utils.errorlog import LuxCoreErrorLog
from ...ui import icons


class LuxCoreNodeVolOutput(bpy.types.Node, LuxCoreNodeOutput):
    """
    Volume output node.
    This is where the export starts (if the output is active).
    """
    bl_label = "Volume Output"
    bl_width_default = 160

    active: BoolProperty(name="Active", default=True, update=update_active)
    id: IntProperty(name="Volume ID", default=-1, min=-1, soft_max=32767,
                     description=MATERIAL_ID_DESC)
    use_photongi: BoolProperty(name="Use PhotonGI Cache", default=False,
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

        layout.prop(self, "id")

        # PhotonGI currently only works with Path engine
        if (context.scene.luxcore.config.photongi.enabled
                and context.scene.luxcore.config.engine == "PATH"):
            # PhotonGI only affects homogeneous and heterogeneous volumes, make the setting inactive for others
            linked_node = self.inputs["Volume"].links[0].from_node if self.inputs["Volume"].is_linked else None
            row = layout.row()
            row.active = bool(linked_node and linked_node.bl_idname in {"LuxCoreNodeVolHomogeneous",
                                                                        "LuxCoreNodeVolHeterogeneous"})
            row.prop(self, "use_photongi")

            world = context.scene.world
            if self.use_photongi and world and world.luxcore.volume == self.id_data:
                col = layout.column(align=True)
                col.label(text="PhotonGI on the world volume can", icon=icons.WARNING)
                col.label(text="lead to VERY long cache computation time!")

    def export(self, exporter, depsgraph, props, luxcore_name):
        prefix = "scene.volumes." + luxcore_name + "."
        definitions = {}
        # Invalidate node cache
        # TODO have one global properties object so this is no longer necessary
        exporter.node_cache.clear()

        if self.inputs["Volume"].is_linked:
            self.inputs["Volume"].export(exporter, depsgraph, props, luxcore_name)
        else:
            # We need a fallback (black volume)
            msg = 'Node "%s" in tree "%s": No volume attached' % (self.name, self.id_data.name)
            LuxCoreErrorLog.add_warning(msg)

            definitions["type"] = "clear"
            definitions["absorption"] = [100, 100, 100]

        definitions["photongi.enable"] = self.use_photongi

        if self.id != -1:
            # LuxCore only assigns a random ID if the ID is not set at all
            definitions["id"] = self.id

        props.Set(utils.create_props(prefix, definitions))

import math
import bpy
from bpy.props import (
    FloatProperty, BoolProperty, StringProperty,
    IntProperty, EnumProperty, PointerProperty
)
from .. import LuxCoreNode
from ...properties.light import (
    POWER_DESCRIPTION, EFFICACY_DESCRIPTION, SAMPLES_DESCRIPTION,
    SPREAD_ANGLE_DESCRIPTION, LIGHTGROUP_DESC, IMPORTANCE_DESCRIPTION,
)
from ...properties.ies import LuxCoreIESProps
from ...export import light


class LuxCoreNodeMatEmission(LuxCoreNode):
    """
    Emission node.

    Note: this is not a material node.
    The emission node is plugged into a material node.
    It is just a group of values, because otherwise every
    material node would contain dozens of sockets
    """
    bl_label = "Emission"
    bl_width_default = 160

    gain = FloatProperty(name="Gain", default=1, min=0, description="Brightness multiplier")
    power = FloatProperty(name="Power (W)", default=100, min=0, description=POWER_DESCRIPTION)
    efficacy = FloatProperty(name="Efficacy (lm/W)", default=17, min=0, description=EFFICACY_DESCRIPTION)
    ies = PointerProperty(type=LuxCoreIESProps)
    samples = IntProperty(name="Samples", default=-1, min=-1, description=SAMPLES_DESCRIPTION)
    importance = FloatProperty(name="Importance", default=1, min=0, description=IMPORTANCE_DESCRIPTION)
    # We use unit="ROTATION" because angles are radians, so conversion is necessary for the UI
    spread_angle = FloatProperty(name="Spread Angle", default=math.pi / 2, min=0, soft_min=math.radians(5),
                                 max=math.pi / 2, subtype="ANGLE", unit="ROTATION",
                                 description=SPREAD_ANGLE_DESCRIPTION)
    lightgroup = StringProperty(name="Light Group", description=LIGHTGROUP_DESC)
    # TODO: mapfile and gamma?

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", (1, 1, 1))

        self.outputs.new("LuxCoreSocketMatEmission", "Emission")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "gain")
        col.prop(self, "power")
        col.prop(self, "efficacy")

        col = layout.column(align=True)
        col.prop(self, "samples")
        col.prop(self, "importance")

        lightgroups = context.scene.luxcore.lightgroups
        layout.prop_search(self, "lightgroup",
                           lightgroups, "custom",
                           icon="OUTLINER_OB_LAMP", text="")

        layout.prop(self, "spread_angle", slider=True)

        # IES Data
        col = layout.column(align=True)
        col.prop(self.ies, "use", toggle=True)

        if self.ies.use:
            box = col.box()

            row = box.row()
            row.label("Source:")
            row.prop(self.ies, "file_type", expand=True)

            if self.ies.file_type == "TEXT":
                box.prop(self.ies, "file_text")
                iesfile = self.ies.file_text
            else:
                # self.iesfile_type == "PATH":
                box.prop(self.ies, "file_path")
                iesfile = self.ies.file_path

            sub = box.column(align=True)
            sub.active = bool(iesfile)
            sub.prop(self.ies, "flipz")
            sub.prop(self.ies, "map_width")
            sub.prop(self.ies, "map_height")

    def export(self, props, definitions):
        """
        The export method is different because this is not a normal material node.
        It is called from LuxCoreNodeMaterial.export_common_props()
        """
        definitions["emission"] = self.inputs["Color"].export(props)
        definitions["emission.gain"] = [self.gain] * 3
        definitions["emission.power"] = self.power
        definitions["emission.efficency"] = self.efficacy
        definitions["emission.samples"] = self.samples
        definitions["emission.importance"] = self.importance
        definitions["emission.theta"] = math.degrees(self.spread_angle)
        lightgroups = bpy.context.scene.luxcore.lightgroups
        definitions["emission.id"] = lightgroups.get_id_by_name(self.lightgroup)

        if self.ies.use:
            try:
                light.export_ies(definitions, self.ies, self.id_data.library, is_meshlight=True)
            except OSError as error:
                msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
                bpy.context.scene.luxcore.errorlog.add_warning(msg)

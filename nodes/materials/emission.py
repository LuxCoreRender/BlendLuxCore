import math
import bpy
from bpy.props import (
    FloatProperty, BoolProperty, StringProperty,
    IntProperty, EnumProperty, PointerProperty
)
from .. import LuxCoreNode
from ...properties.light import (
    POWER_DESCRIPTION, EFFICACY_DESCRIPTION, SAMPLES_DESCRIPTION,
    IES_FILE_DESCRIPTION, IES_TEXT_DESCRIPTION, iesfile_type_items,
    SPREAD_ANGLE_DESCRIPTION, USE_IES_DESCRIPTION
)
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
    bl_width_min = 160

    gain = FloatProperty(name="Gain", default=1, min=0, description="Brightness multiplier")
    power = FloatProperty(name="Power (W)", default=100, min=0, description=POWER_DESCRIPTION)
    efficacy = FloatProperty(name="Efficacy (lm/W)", default=17, min=0, description=EFFICACY_DESCRIPTION)
    use_ies = BoolProperty(name="Use IES File", default=False, description=USE_IES_DESCRIPTION)
    iesfile_type = EnumProperty(name="IES File Type", items=iesfile_type_items, default="TEXT")
    iesfile_path = StringProperty(name="File", subtype="FILE_PATH", description=IES_FILE_DESCRIPTION)
    iesfile_text = PointerProperty(name="Text", type=bpy.types.Text, description=IES_TEXT_DESCRIPTION)
    flipz = BoolProperty(name="Flip IES Z Axis", default=False)
    samples = IntProperty(name="Samples", default=-1, min=-1, description=SAMPLES_DESCRIPTION)
    # We use unit="ROTATION" because angles are radians, so conversion is necessary for the UI
    spread_angle = FloatProperty(name="Spread Angle", default=math.pi / 2, min=0, soft_min=math.radians(5),
                                 max=math.pi / 2, subtype="ANGLE", unit="ROTATION",
                                 description=SPREAD_ANGLE_DESCRIPTION)
    # TODO: mapfile and gamma?
    # TODO: lightgroup

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", (1, 1, 1))

        self.outputs.new("LuxCoreSocketMatEmission", "Emission")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "gain")
        col.prop(self, "power")
        col.prop(self, "efficacy")

        layout.prop(self, "spread_angle", slider=True)

        # IES Data
        col = layout.column()
        col.prop(self, "use_ies", toggle=True)

        if self.use_ies:
            row = col.row()
            row.label("Source:")
            row.prop(self, "iesfile_type", expand=True)

            if self.iesfile_type == "TEXT":
                col.prop(self, "iesfile_text")
                iesfile = self.iesfile_text
            else:
                # self.iesfile_type == "PATH":
                col.prop(self, "iesfile_path")
                iesfile = self.iesfile_path

            sub = col.column()
            sub.active = bool(iesfile)
            sub.prop(self, "flipz")

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
        definitions["emission.theta"] = math.degrees(self.spread_angle)

        if self.use_ies:
            try:
                light.export_ies(definitions, self.iesfile_type, self.iesfile_text,
                                 self.iesfile_path, self.flipz, self.id_data.library, is_meshlight=True)
            except OSError as error:
                msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
                bpy.context.scene.luxcore.errorlog.add_warning(msg)

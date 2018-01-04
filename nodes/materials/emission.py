import bpy
from bpy.props import FloatProperty, BoolProperty, StringProperty, IntProperty
from .. import LuxCoreNode
from ...properties.light import POWER_DESCRIPTION, EFFICACY_DESCRIPTION, SAMPLES_DESCRIPTION


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
    iesfile = StringProperty(name="IES File", subtype="FILE_PATH")
    flipz = BoolProperty(name="Flip IES Z Axis", default=False)
    samples = IntProperty(name="Samples", default=-1, min=-1, description=SAMPLES_DESCRIPTION)
    # TODO: mapfile and gamma?
    # TODO: lightgroup
    # TODO: theta (spread angle)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", (1, 1, 1))

        self.outputs.new("LuxCoreSocketMatEmission", "Emission")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "gain")
        col.prop(self, "power")
        col.prop(self, "efficacy")

        col = layout.column(align=True)
        col.prop(self, "iesfile")
        if self.iesfile:
            col.prop(self, "flipz")

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
        if self.iesfile:
            # TODO: error if iesfile does not exist (also resolve relative paths etc.)
            definitions["emission.iesfile"] = self.iesfile
            definitions["emission.flipz"] = self.flipz

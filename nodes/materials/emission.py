import bpy
from bpy.props import (
    FloatProperty, BoolProperty, StringProperty,
    IntProperty, EnumProperty, PointerProperty
)
from .. import LuxCoreNode
from ...properties.light import (
    POWER_DESCRIPTION, EFFICACY_DESCRIPTION, SAMPLES_DESCRIPTION,
    IES_FILE_DESCRIPTION, IES_TEXT_DESCRIPTION, iesfile_type_items
)
from ... import utils


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
    iesfile_type = EnumProperty(name="IES File Type", items=iesfile_type_items, default="TEXT")
    iesfile_path = StringProperty(name="IES File", subtype="FILE_PATH", description=IES_FILE_DESCRIPTION)
    iesfile_text = PointerProperty(name="IES Text", type=bpy.types.Text, description=IES_TEXT_DESCRIPTION)
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

        # IES Data
        col = layout.column()
        row = col.row()
        row.label("IES Data:")
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

        has_ies = (self.iesfile_type == "TEXT" and self.iesfile_text) or (self.iesfile_type == "PATH" and self.iesfile_path)
        if has_ies:
            definitions["emission.flipz"] = self.flipz

            # There are two ways to specify IES data: filepath or blob (ascii text)
            if self.iesfile_type == "TEXT":
                # Blender text block
                text = self.iesfile_text

                if text:
                    blob = text.as_string().encode("ascii")

                    if blob:
                        definitions["emission.iesblob"] = [blob]
            else:
                # File path
                iesfile = self.iesfile_path

                if iesfile:
                    filepath = utils.get_abspath(iesfile, self.id_data.library, must_exist=True, must_be_file=True)

                    if filepath:
                        definitions["emission.iesfile"] = filepath
                    else:
                        error = 'Could not find .ies file at path "%s"' % iesfile
                        msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
                        bpy.context.scene.luxcore.errorlog.add_warning(msg)

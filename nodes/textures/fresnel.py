import bpy
from bpy.props import PointerProperty, EnumProperty
from .. import LuxCoreNodeTexture
from ... import utils


class LuxCoreNodeTexFresnel(LuxCoreNodeTexture):
    bl_label = "Fresnel"
    bl_width_min = 200
    
    def change_input_type(self, context):
        self.inputs["Reflection Color"].enabled = self.input_type == "color"

    input_type_items = [
        ("color", "Color", "Use custom color as input"),
        ("preset", "Preset", "Use a Preset fresnel texture as input"),
        ("nk", "File", "Use a fresnel texture file (.nk) as input")
    ]

    preset_items = [
                ("amorphous carbon", "Amorphous carbon", "amorphous carbon"),
                ("copper", "Copper", "copper"),
                ("gold", "Gold", "gold"),
                ("silver", "Silver", "silver"),
                ("aluminium", "Aluminium", "aluminium")
    ]

    input_type = EnumProperty(name="Type", description="Input Type", items=input_type_items, default="color",
                                        update=change_input_type)

    preset = EnumProperty(name="Preset", description="NK data presets", items=preset_items,
                                           default="aluminium")


    filepath = bpy.props.StringProperty(name="Nk File", description="Nk file path", subtype="FILE_PATH")


    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Reflection Color", (0.7, 0.7, 0.7))
        self.outputs.new("LuxCoreSocketFresnel", "Fresnel")

    def draw_buttons(self, context, layout):
        layout.prop(self, "input_type", expand=True)
        
        if self.input_type == "preset":
            layout.prop(self, "preset")

        if self.input_type == "nk":
            layout.prop(self, "filepath")

    def export(self, props, luxcore_name=None):
        if self.input_type == "color":
            definitions = {
                "type": "fresnelcolor",
                "kr": self.inputs["Reflection Color"].export(props),
            }
        elif self.input_type == "preset":
            definitions = {
                "type": "fresnelpreset",
                "name": self.preset,
            }
        else:
            #Fresnel data file
            filepath = utils.get_abspath(self.filepath, must_exist=True, must_be_file=True)

            if filepath:
                definitions = {
                    "type": "fresnelsopra",
                    "file": filepath,
                }
            else:
                # Fallback, file not found
                error = 'Could not find .nk file at path "%s"' % self.filepath
                msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
                bpy.context.scene.luxcore.errorlog.add_warning(msg)

                definitions = {
                    "type": "fresnelcolor",
                    "kr": [0, 0, 0],
                }
        
        return self.base_export(props, definitions, luxcore_name)

from bpy.props import FloatProperty, EnumProperty
from .. import LuxCoreNodeMaterial
from ..sockets import LuxCoreSocketFloat
from ...ui import icons

REFLECTION_DESCRIPTION = "Glossy layer reflection value"


class LuxCoreSocketReflection(LuxCoreSocketFloat):
    # Reflections look weird when roughness gets too small
    default_value = FloatProperty(min=0.00001, max=1, description=REFLECTION_DESCRIPTION)
    slider = True


class LuxCoreNodeMatCarpaint(LuxCoreNodeMaterial):
    """
    carpaint material node

    Note about the parameters:
    R1, R2, R3 seem to be "reflection" values, whatever that means.
    M1, M2, M3 seem to be roughness values for the reflection values.
    """
    bl_label = "Carpaint Material"
    bl_width_default = 200

    def update_preset(self, context):
        enabled = self.preset == "manual"

        self.inputs['Diffuse Color'].enabled = enabled
        self.inputs['Specular Color 1'].enabled = enabled
        self.inputs['Specular Color 2'].enabled = enabled
        self.inputs['Specular Color 3'].enabled = enabled
        self.inputs['M1'].enabled = enabled
        self.inputs['M2'].enabled = enabled
        self.inputs['M3'].enabled = enabled
        self.inputs['R1'].enabled = enabled
        self.inputs['R2'].enabled = enabled
        self.inputs['R3'].enabled = enabled

    preset_items = [
        ("manual", "Manual settings", "", 0),
        ("2k acrylack", "2k Acrylack", "", 1),
        ("blue", "Blue", "", 2),
        ("blue matte", "Blue Matte", "", 3),
        ("bmw339", "BMW 339", "", 4),
        ("ford f8", "Ford F8", "", 5),
        ("opel titan", "Opel Titan", "", 6),
        ("polaris silber", "Polaris Silber", "", 7),
        ("white", "White", "", 8),
    ]
    preset = EnumProperty(name="Preset", items=preset_items, default="manual", update=update_preset)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Diffuse Color", (0.3, 0.3, 0.3))
        self.add_input("LuxCoreSocketColor", "Specular Color 1", (1, 1, 1))
        self.add_input("LuxCoreSocketReflection", "R1", 0.95)
        self.add_input("LuxCoreSocketRoughness", "M1", 0.25)
        self.add_input("LuxCoreSocketColor", "Specular Color 2", (1, 1, 1))
        self.add_input("LuxCoreSocketReflection", "R2", 0.9)
        self.add_input("LuxCoreSocketRoughness", "M2", 0.1)
        self.add_input("LuxCoreSocketColor", "Specular Color 3", (1, 1, 1))
        self.add_input("LuxCoreSocketReflection", "R3", 0.7)
        self.add_input("LuxCoreSocketRoughness", "M3", 0.015)
        self.add_input("LuxCoreSocketColor", "Absorption Color", (0, 0, 0))
        self.add_input("LuxCoreSocketFloatPositive", "Absorption Depth (nm)", 0)
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        op = layout.operator("luxcore.open_website", text="Open Wiki Page", icon=icons.URL)
        op.url = "https://wiki.luxcorerender.org/LuxCoreRender_Materials_Car_Paint"
        layout.prop(self, "preset")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "carpaint",
            "kd": self.inputs["Diffuse Color"].export(exporter, props),
            "ka": self.inputs["Absorption Color"].export(exporter, props),
            "ks1": self.inputs["Specular Color 1"].export(exporter, props),
            "ks2": self.inputs["Specular Color 2"].export(exporter, props),
            "ks3": self.inputs["Specular Color 3"].export(exporter, props),
            "d": self.inputs["Absorption Depth (nm)"].export(exporter, props),
            "m1": self.inputs["M1"].export(exporter, props),
            "m2": self.inputs["M2"].export(exporter, props),
            "m3": self.inputs["M3"].export(exporter, props),
            "r1": self.inputs["R1"].export(exporter, props),
            "r2": self.inputs["R2"].export(exporter, props),
            "r3": self.inputs["R3"].export(exporter, props),
        }

        if self.preset != "manual":
            definitions["preset"] = self.preset

        self.export_common_inputs(exporter, props, definitions)
        return self.create_props(props, definitions, luxcore_name)

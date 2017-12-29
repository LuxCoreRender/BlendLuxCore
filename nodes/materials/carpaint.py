import bpy
from bpy.props import FloatProperty
from .. import LuxCoreNodeMaterial
from ..sockets import LuxCoreSocketFloat, LuxCoreSocketRoughness

DEPTH_DESCRIPTION = "Absortion depth (nm) value"
REFLECTION_DESCRIPTION = "Glossy layer reflection value"


class LuxCoreSocketDepth(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0.0, description=DEPTH_DESCRIPTION)
    slider = True

class LuxCoreSocketReflection(LuxCoreSocketFloat):
    # Reflections look weird when roughness gets too small
    default_value = FloatProperty(min=0.0, description=REFLECTION_DESCRIPTION)
    slider = True


class LuxCoreNodeMatCarpaint(LuxCoreNodeMaterial):
    """carpaint material node"""
    bl_label = "Carpaint Material"
    bl_width_min = 160

    depth = FloatProperty(name="Absorption depth (nm)", default=0, min=0, description=DEPTH_DESCRIPTION)
    
    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Diffuse Color", (1, 1, 1))
        self.add_input("LuxCoreSocketColor", "Specular Color 1", (1, 1, 1))
        self.add_input("LuxCoreSocketRoughness", "R1", 1)
        self.add_input("LuxCoreSocketReflection", "M1", 0)
        self.add_input("LuxCoreSocketColor", "Specular Color 2", (1, 1, 1))
        self.add_input("LuxCoreSocketRoughness", "R2", 1)
        self.add_input("LuxCoreSocketReflection", "M2", 0)
        self.add_input("LuxCoreSocketColor", "Specular Color 3", (1, 1, 1))
        self.add_input("LuxCoreSocketRoughness", "R3", 1)
        self.add_input("LuxCoreSocketReflection", "M3", 0)
        self.add_input("LuxCoreSocketColor", "Absorption Color", (0, 0, 0))
        self.add_input("LuxCoreSocketDepth", "Absorption Depth (nm)", 0)
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "carpaint",
            "kd": self.inputs["Diffuse Color"].export(props),
            "ka": self.inputs["Absorption Color"].export(props),
            "ks1": self.inputs["Specular Color 1"].export(props),
            "ks2": self.inputs["Specular Color 2"].export(props),
            "ks3": self.inputs["Specular Color 3"].export(props),
            "d": self.inputs["Absorption Depth (nm)"].export(props),
            "m1": self.inputs["M1"].export(props),
            "m2": self.inputs["M2"].export(props),
            "m3": self.inputs["M3"].export(props),
            "r1": self.inputs["R1"].export(props),
            "r2": self.inputs["R2"].export(props),
            "r3": self.inputs["R3"].export(props),
        }
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)

import bpy
from bpy.props import BoolProperty
from ..base import LuxCoreNodeMaterial, ThinFilmCoating
from .glass import THIN_FILM_DESCRIPTION


class LuxCoreNodeMatDisney(LuxCoreNodeMaterial, bpy.types.Node):
    bl_label = "Disney Material"
    bl_width_default = 190
    
    def update_use_thinfilmcoating(self, context):
        id = self.inputs.find("Film Amount")
        self.inputs[id].enabled = self.use_thinfilmcoating
        ThinFilmCoating.toggle(self, context)
    
    use_thinfilmcoating: BoolProperty(name="Thin Film Coating", default=False,
                                      description=THIN_FILM_DESCRIPTION,
                                      update=update_use_thinfilmcoating)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Base Color", [0.7] * 3)
        self.add_input("LuxCoreSocketFloat0to1", "Subsurface", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Metallic", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Specular", 0.5)
        self.add_input("LuxCoreSocketFloat0to1", "Specular Tint", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Roughness", 0.2)
        self.add_input("LuxCoreSocketFloat0to1", "Anisotropic", 0)
        self.add_input("LuxCoreSocketFloatDisneySheen", "Sheen", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Sheen Tint", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Clearcoat", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Clearcoat Gloss", 1)
        self.add_input("LuxCoreSocketFloat0to1", "Film Amount", 1, enabled=False)
        ThinFilmCoating.init(self)
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "use_thinfilmcoating")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "disney",
            "basecolor": self.inputs["Base Color"].export(exporter, depsgraph, props),
            "subsurface": self.inputs["Subsurface"].export(exporter, depsgraph, props),
            "metallic": self.inputs["Metallic"].export(exporter, depsgraph, props),
            "specular": self.inputs["Specular"].export(exporter, depsgraph, props),
            "speculartint": self.inputs["Specular Tint"].export(exporter, depsgraph, props),
            "roughness": self.inputs["Roughness"].export(exporter, depsgraph, props),
            "anisotropic": self.inputs["Anisotropic"].export(exporter, depsgraph, props),
            "sheen": self.inputs["Sheen"].export(exporter, depsgraph, props),
            "sheentint": self.inputs["Sheen Tint"].export(exporter, depsgraph, props),
            "clearcoat": self.inputs["Clearcoat"].export(exporter, depsgraph, props),
            "clearcoatgloss": self.inputs["Clearcoat Gloss"].export(exporter, depsgraph, props),
        }
        
        if self.use_thinfilmcoating:
            amount_socket = self.inputs["Film Amount"]
            amount = amount_socket.export(exporter, depsgraph, props)
            
            if amount_socket.is_linked or amount > 0:
                definitions["filmamount"] = amount
                ThinFilmCoating.export(self, exporter, depsgraph, props, definitions)

        self.export_common_inputs(exporter, depsgraph, props, definitions)
        return self.create_props(props, definitions, luxcore_name)

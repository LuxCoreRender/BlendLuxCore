import bpy
from bpy.props import BoolProperty
from ..base import LuxCoreNodeMaterial, Roughness
from ...utils import node as utils_node


IOR_DESCRIPTION = (
    "Specify index of refraction to control reflection brightness, instead of using the specular color. "
    "This is useful if you know the IOR of the coating material. Note that the material will have physically "
    "correct fresnel falloff in the specular reflections regardless if specular color or IOR is used to "
    "specify reflection strength"
)

MULTIBOUNCE_DESCRIPTION = (
    "Simulate multiple bounces in the glossy coating (not counting as actual light ray bounce). "
    "Gives the material a fuzzy sheen"
)


class LuxCoreNodeMatGlossyTranslucent(LuxCoreNodeMaterial, bpy.types.Node):
    bl_label = "Glossy Translucent Material"
    bl_width_default = 160

    def update_use_ior(self, context):
        id = self.inputs.find("IOR")
        self.inputs[id].enabled = self.use_ior

        id = self.inputs.find("Specular Color")
        self.inputs[id].enabled = not self.use_ior
        utils_node.force_viewport_update(self, context)

    def update_use_ior_bf(self, context):
        id = self.inputs.find("BF IOR")
        self.inputs[id].enabled = self.use_ior_bf

        id = self.inputs.find("BF Specular Color")
        self.inputs[id].enabled = not self.use_ior_bf
        utils_node.force_viewport_update(self, context)

    def update_use_backface(self, context):
        # Note: these are the names (strings), not references to the sockets
        sockets = [socket for socket in self.inputs.keys() if socket.startswith("BF ")]

        for socket in sockets:
            id = self.inputs.find(socket)
            if socket == "BF V-Roughness":
                self.inputs[id].enabled = self.use_backface and self.use_anisotropy
            elif socket == "BF IOR":
                self.inputs[id].enabled = self.use_backface and self.use_ior_bf
            elif socket == "BF Specular Color":
                self.inputs[id].enabled = self.use_backface and not self.use_ior_bf
            else:
                self.inputs[id].enabled = self.use_backface

        if context:
            utils_node.force_viewport_update(self, context)

    # This enables/disables anisotropic roughness for both front and back face
    use_anisotropy: BoolProperty(name=Roughness.aniso_name,
                                  default=False,
                                  description=Roughness.aniso_desc,
                                  update=Roughness.update_anisotropy)

    # Front face
    multibounce: BoolProperty(name="Multibounce", default=False,
                               description=MULTIBOUNCE_DESCRIPTION)
    use_ior: BoolProperty(name="Use IOR", default=False,
                           update=update_use_ior,
                           description=IOR_DESCRIPTION)

    # Back face
    use_backface: BoolProperty(name="Double Sided", default=False,
                                update=update_use_backface,
                                description="Enable if used on a 2D mesh, e.g. on tree leaves")
    multibounce_bf: BoolProperty(update=utils_node.force_viewport_update, name="BF Multibounce", default=False,
                                  description=MULTIBOUNCE_DESCRIPTION + " (backface)")
    use_ior_bf: BoolProperty(name="BF Use IOR", default=False,
                              update=update_use_ior_bf,
                              description=IOR_DESCRIPTION + " (backface)")

    def init(self, context):
        default_roughness = 0.05

        self.add_input("LuxCoreSocketColor", "Diffuse Color", [0.5] * 3)
        self.add_input("LuxCoreSocketColor", "Transmission Color", [0.5] * 3)

        # Front face
        self.add_input("LuxCoreSocketColor", "Specular Color", [0.05] * 3)
        self.add_input("LuxCoreSocketIOR", "IOR", 1.5)
        self.inputs["IOR"].enabled = False
        self.add_input("LuxCoreSocketColor", "Absorption Color", [0] * 3)
        self.add_input("LuxCoreSocketFloatPositive", "Absorption Depth (nm)", 0)
        Roughness.init(self, default_roughness)

        # Back face
        self.add_input("LuxCoreSocketColor", "BF Specular Color", [0.05] * 3)
        self.add_input("LuxCoreSocketIOR", "BF IOR", 1.5)
        self.add_input("LuxCoreSocketColor", "BF Absorption Color", [0] * 3)
        self.add_input("LuxCoreSocketFloatPositive", "BF Absorption Depth (nm)", 0)
        Roughness.init_backface(self, default_roughness, init_enabled=False)
        # Back face sockets should be hidden by default
        self.update_use_backface(context)

        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multibounce")
        layout.prop(self, "use_ior")
        Roughness.draw(self, context, layout)

        layout.prop(self, "use_backface", toggle=True)

        if self.use_backface:
            layout.prop(self, "multibounce_bf")
            layout.prop(self, "use_ior_bf")

        utils_node.draw_transmission_info(self, layout)

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "glossytranslucent",
            "kd": self.inputs["Diffuse Color"].export(exporter, depsgraph, props),
            "kt": self.inputs["Transmission Color"].export(exporter, depsgraph, props),

            # Front face (in normal direction)
            "multibounce": self.multibounce,
            "multibounce_bf": self.multibounce,
            "ka": self.inputs["Absorption Color"].export(exporter, depsgraph, props),
            "ka_bf": self.inputs["Absorption Color"].export(exporter, depsgraph, props),
            "d": self.inputs["Absorption Depth (nm)"].export(exporter, depsgraph, props),
            "d_bf": self.inputs["Absorption Depth (nm)"].export(exporter, depsgraph, props),
        }

        if self.use_ior:
            definitions["index"] = self.inputs["IOR"].export(exporter, depsgraph, props)
            definitions["index_bf"] = self.inputs["IOR"].export(exporter, depsgraph, props)
            definitions["ks"] = [1, 1, 1]
            definitions["ks_bf"] = [1, 1, 1]
        else:
            definitions["ks"] = self.inputs["Specular Color"].export(exporter, depsgraph, props)
            definitions["ks_bf"] = self.inputs["Specular Color"].export(exporter, depsgraph, props)

        if self.use_backface:
            definitions.update({
                # Back face (on opposite side of normal)
                "multibounce_bf": self.multibounce_bf,
                "ka_bf": self.inputs["BF Absorption Color"].export(exporter, depsgraph, props),
                "d_bf": self.inputs["BF Absorption Depth (nm)"].export(exporter, depsgraph, props),
            })

            if self.use_ior_bf:
                definitions["index_bf"] = self.inputs["BF IOR"].export(exporter, depsgraph, props)
                definitions["ks_bf"] = [1, 1, 1]
            else:
                definitions["ks_bf"] = self.inputs["BF Specular Color"].export(exporter, depsgraph, props)

        # This includes backface roughness
        Roughness.export(self, exporter, depsgraph, props, definitions)
        self.export_common_inputs(exporter, depsgraph, props, definitions)
        return self.create_props(props, definitions, luxcore_name)

import bpy
from bpy.props import EnumProperty, FloatProperty
from ..base import LuxCoreNodeTexture

from .. import NOISE_BASIS_ITEMS

from ... import utils
from ...utils import node as utils_node

class LuxCoreNodeTexBlenderMusgrave(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Blender Musgrave"
    bl_width_default = 200    

    musgrave_type_items = [
        ("multifractal", "Multifractal", ""),
        ("ridged_multifractal", "Ridged Multifractal", ""),
        ("hybrid_multifractal", "Hybrid Multifractal", ""),
        ("hetero_terrain", "Hetero Terrain", ""),
        ("fbm", "FBM", ""),
    ]

    musgrave_type: EnumProperty(update=utils_node.force_viewport_update, name="Noise Type", description="Type of noise used", items=musgrave_type_items, default="multifractal")
    noise_basis: EnumProperty(update=utils_node.force_viewport_update, name="Basis", description="Basis of noise used", items=NOISE_BASIS_ITEMS, default="blender_original")
    noise_size: FloatProperty(update=utils_node.force_viewport_update, name="Noise Size", default=0.25, min=0)
    h: FloatProperty(update=utils_node.force_viewport_update, name="Dimension", default=1.0, min=0)
    lacu: FloatProperty(update=utils_node.force_viewport_update, name="Lacunarity", default=2.0)
    octs: FloatProperty(update=utils_node.force_viewport_update, name="Octaves", default=2.0, min=0)
    offset: FloatProperty(update=utils_node.force_viewport_update, name="Offset", default=1.0)
    gain: FloatProperty(update=utils_node.force_viewport_update, name="Gain", default=1.0, min=0)
    iscale: FloatProperty(update=utils_node.force_viewport_update, name="Intensity", default=1.0)
    bright: FloatProperty(update=utils_node.force_viewport_update, name="Brightness", default=1.0, min=0)
    contrast: FloatProperty(update=utils_node.force_viewport_update, name="Contrast", default=1.0, min=0)

    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "musgrave_type")
        layout.prop(self, "noise_basis")

        col = layout.column(align=True)
        col.prop(self, "noise_size")
        col.prop(self, "h")
        col.prop(self, "lacu")
        col.prop(self, "octs")

        col = layout.column(align=True)

        if self.musgrave_type in ("ridged_multifractal", "hybrid_multifractal", "hetero_terrain"):
            col.prop(self, "offset")

        if self.musgrave_type in ("ridged_multifractal", "hybrid_multifractal"):
            col.prop(self, "gain")

        if self.musgrave_type != "fbm":
            col.prop(self, "iscale")

        column = layout.column(align=True)
        column.prop(self, "bright")
        column.prop(self, "contrast")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        mapping_type, uvindex, transformation = self.inputs["3D Mapping"].export(exporter, depsgraph, props)
       
        definitions = {
            "type": "blender_musgrave",
            "musgravetype": self.musgrave_type,
            "noisebasis": self.noise_basis,
            "noisesize": self.noise_size,
            "h": self.h,
            "lacu": self.lacu,
            "octs": self.octs,
            "bright": self.bright,
            "contrast": self.contrast,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation),
        }
        if self.musgrave_type in ('ridged_multifractal', 'hybrid_multifractal', 'hetero_terrain'):
            definitions["offset"] = self.offset

        if self.musgrave_type in ('ridged_multifractal', 'hybrid_multifractal'):
            definitions["gain"] = self.gain

        if self.musgrave_type != 'fbm':
            definitions["iscale"] = self.iscale            
        
        if mapping_type == "uvmapping3d":
            definitions["mapping.uvindex"] = uvindex

        return self.create_props(props, definitions, luxcore_name)

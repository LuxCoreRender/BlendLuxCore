from bpy.props import EnumProperty, FloatProperty
from .. import LuxCoreNodeTexture

from ... import utils


class LuxCoreNodeTexBlenderVoronoi(LuxCoreNodeTexture):
    bl_label = "Blender Voronoi"
    bl_width_default = 200

    distance_items = [
        ("actual_distance", "Actual Distance", "actual distance"),
        ("distance_squared", "Distance Squared", "distance squared"),
        ("manhattan", "Manhattan", "manhattan"),
        ("chebychev", "Chebychev", "chebychev"),
        ("minkovsky_half", "Minkowsky 1/2", "minkowsky half"),
        ("minkovsky_four", "Minkowsky 4", "minkowsky four"),
        ("minkovsky", "Minkowsky", "minkowsky"),
    ]

    dist_metric = EnumProperty(name="Distance Metric", description="Algorithm used to calculate distance of sample points to feature points",
                                        items=distance_items, default="actual_distance")
    minkowsky_exp = FloatProperty(name="Exponent", default=1.0)
    noise_size = FloatProperty(name="Noise Size", default=0.25, min=0)    
    w1 = FloatProperty(name="Weight 1", default=1.0, min=-2, max=2, subtype="FACTOR")
    w2 = FloatProperty(name="Weight 2", default=0.0, min=-2, max=2, subtype="FACTOR")
    w3 = FloatProperty(name="Weight 3", default=0.0, min=-2, max=2, subtype="FACTOR")
    w4 = FloatProperty(name="Weight 4", default=0.0, min=-2, max=2, subtype="FACTOR")
    bright = FloatProperty(name="Brightness", default=1.0, min=0)
    contrast = FloatProperty(name="Contrast", default=1.0, min=0)

    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "dist_metric")
        if self.dist_metric == "minkovsky":
            layout.prop(self, "minkowsky_exp")
        layout.prop(self, "noise_size")
        column = layout.column(align=True)
        column.prop(self, "w1")
        column.prop(self, "w2")
        column.prop(self, "w3")
        column.prop(self, "w4")

        column = layout.column(align=True)
        column.prop(self, "bright")
        column.prop(self, "contrast")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, props)
       
        definitions = {
            "type": "blender_voronoi",
            "distmetric": self.dist_metric,
            "w1": self.w1,
            "w2": self.w2,
            "w3": self.w3,
            "w4": self.w4,
            "noisesize": self.noise_size,
            "bright": self.bright,
            "contrast": self.contrast,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }
        if self.dist_metric == "minkovsky":
            definitions["exponent"] = self.minkowsky_exp

        
        return self.create_props(props, definitions, luxcore_name)

import bpy
from bpy.props import PointerProperty, EnumProperty
from .. import LuxCoreNodeTexture
from ...export.image import ImageExporter
from ...utils import node as utils_node


class LuxCoreNodeTexImagemap(LuxCoreNodeTexture):
    bl_label = "Imagemap"
    bl_width_min = 200

    image = PointerProperty(name="Image", type=bpy.types.Image)

    channel_items = [
        ("default", "Default", "Do not convert the image cannels", 0),
        ("rgb", "RGB", "Use RGB color channels", 1),
        ("red", "Red", "Use only the red color channel", 2),
        ("green", "Green", "Use only the green color channel", 3),
        ("blue", "Blue", "Use only the blue color channel", 4),
        ("alpha", "Alpha", "Use only the alpha channel", 5),
        ("mean", "Mean", "Greyscale", 6),
        ("colored_mean", "Colored Mean", "Greyscale", 7),
    ]
    channel = EnumProperty(name="Channel", items=channel_items, default="default")

    wrap_items = [
        ("repeat", "Repeat", "", 0),
        ("clamp", "Clamp", "", 3),
        ("black", "Black", "", 1),
        ("white", "White", "", 2),
    ]
    wrap = EnumProperty(name="Wrap", items=wrap_items, default="repeat")

    def init(self, context):
        self.add_input("LuxCoreSocketFloatPositive", "Gamma", 2.2)
        self.add_input("LuxCoreSocketFloatPositive", "Gain", 1)
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.template_ID(self, "image", open="image.open")

        if self.image:
            layout.prop(self, "channel")
            layout.prop(self, "wrap")

        # Info about UV mapping (only show if default is used,
        # when no mapping node is linked)
        if not self.inputs["2D Mapping"].is_linked:
            utils_node.draw_uv_info(context, layout)

    def export(self, props, luxcore_name=None):
        uvscale, uvdelta = self.inputs["2D Mapping"].export(props)

        definitions = {
            "type": "imagemap",
            "file": ImageExporter.export(self.image),
            "gamma": self.inputs["Gamma"].export(props),
            "gain": self.inputs["Gain"].export(props),
            "channel": self.channel,
            "wrap": self.wrap,
            # Mapping
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": uvscale,
            "mapping.uvdelta": uvdelta,
        }
        return self.base_export(props, definitions, luxcore_name)

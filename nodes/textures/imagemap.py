import bpy
from bpy.props import PointerProperty, EnumProperty, BoolProperty, FloatProperty
from .. import LuxCoreNodeTexture
from ...export.image import ImageExporter
from ...utils import node as utils_node
from ... import utils


NORMAL_SCALE_DESC = "Height multiplier, used to adjust the baked-in height of the normal map"


class LuxCoreNodeTexImagemap(LuxCoreNodeTexture):
    bl_label = "Imagemap"
    bl_width_default = 200

    def update_image(self, context):
        if self.image:
            # Seems like we still need this.
            # User counting does not work reliably with Python PointerProperty.
            # Sometimes, this node is not counted as user.
            self.image.use_fake_user = True

    image = PointerProperty(name="Image", type=bpy.types.Image, update=update_image)

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

    def update_is_normal_map(self, context):
        self.outputs["Color"].enabled = not self.is_normal_map
        self.outputs["Bump"].enabled = self.is_normal_map

    is_normal_map = BoolProperty(name="Normalmap", default=False, update=update_is_normal_map,
                                 description="Might want to enable this if the image looks blue")
    normal_map_scale = FloatProperty(name="Height", default=1, min=0, soft_max=5,
                                     description=NORMAL_SCALE_DESC)

    def init(self, context):
        self.add_input("LuxCoreSocketFloatPositive", "Gamma", 2.2)
        self.add_input("LuxCoreSocketFloatPositive", "Brightness", 1)
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")
        self.outputs.new("LuxCoreSocketBump", "Bump")
        self.outputs["Bump"].enabled = False

    def draw_label(self):
        if self.image:
            return self.image.name
        else:
            return self.bl_label

    def draw_buttons(self, context, layout):
        layout.template_ID(self, "image", open="image.open")

        col = layout.column()
        col.active = self.image is not None

        col.prop(self, "channel")
        col.prop(self, "wrap")

        # Info about UV mapping (only show if default is used,
        # when no mapping node is linked)
        if not self.inputs["2D Mapping"].is_linked:
            utils_node.draw_uv_info(context, col)

        col.prop(self, "is_normal_map")
        if self.is_normal_map:
            col.prop(self, "normal_map_scale")

    def export(self, props, luxcore_name=None):
        if self.image is None:
            return [0, 0, 0]

        try:
            filepath = ImageExporter.export(self.image)
        except OSError as error:
            msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
            bpy.context.scene.luxcore.errorlog.add_warning(msg)
            return [1, 0, 1]

        # TODO remove this in the future, e.g. after alpha2 or 3 release
        if "Brightness" not in self.inputs:
            error = "Outdated node! Replace with new imagemap node."
            msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
            bpy.context.scene.luxcore.errorlog.add_warning(msg)
            print(msg)
            return [0, 0, 0]

        uvscale, uvdelta = self.inputs["2D Mapping"].export(props)

        definitions = {
            "type": "imagemap",
            "file": filepath,
            "gamma": self.inputs["Gamma"].export(props),
            "gain": self.inputs["Brightness"].export(props),
            "channel": self.channel,
            "wrap": self.wrap,
            # Mapping
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": uvscale,
            "mapping.uvdelta": uvdelta,
        }

        luxcore_name = self.base_export(props, definitions, luxcore_name)

        if self.is_normal_map and self.normal_map_scale > 0:
            # Implicitly create a normalmap
            tex_name = luxcore_name + "_normalmap"
            helper_prefix = "scene.textures." + tex_name + "."
            helper_defs = {
                "type": "normalmap",
                "texture": luxcore_name,
                "scale": self.normal_map_scale,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))

            # The helper texture gets linked in front of this node
            return tex_name
        else:
            return luxcore_name

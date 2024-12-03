import bpy
from bpy.props import (
    PointerProperty, EnumProperty, StringProperty, IntProperty,
    BoolProperty, FloatProperty,
)
from ..base import LuxCoreNodeTexture
from ...export.image import ImageExporter
from ...properties.image_user import LuxCoreImageUser
from ... import utils
from ...utils import node as utils_node
from ...utils.errorlog import LuxCoreErrorLog
from ...ui import icons
from ...handlers import frame_change_pre


NORMAL_MAP_DESC = (
    "Enable if this image is a normal map. Only tangent space maps (the most common "
    "normal maps) are supported. Gamma and brightness will be set to 1"
)
NORMAL_SCALE_DESC = "Height multiplier, used to adjust the baked-in height of the normal map"


class LuxCoreNodeTexImagemap(LuxCoreNodeTexture, bpy.types.Node):
    bl_label = "Imagemap"
    bl_width_default = 200

    def update_image(self, context):
        self.image_user.update(self.image)
        if self.image:
            # Seems like we still need this.
            # User counting does not work reliably with Python PointerProperty.
            # Sometimes, this node is not counted as user.
            self.image.use_fake_user = True
        utils_node.force_viewport_update(self, context)

    image: PointerProperty(name="Image", type=bpy.types.Image, update=update_image)
    image_user: PointerProperty(update=utils_node.force_viewport_update, type=LuxCoreImageUser)

    channel_items = [
        ("default", "Default Channels", "Use the image channels as they are in the file", 0),
        ("rgb", "RGB", "Use RGB color channels", 1),
        ("red", "Red", "Use only the red color channel", 2),
        ("green", "Green", "Use only the green color channel", 3),
        ("blue", "Blue", "Use only the blue color channel", 4),
        ("alpha", "Alpha", "Use only the alpha channel", 5),
        ("mean", "Mean (Average)", "Greyscale", 6),
        ("colored_mean", "Mean (Luminance)", "Greyscale", 7),
    ]
    channel: EnumProperty(update=utils_node.force_viewport_update, name="Channel", 
                          items=channel_items, default="default", description="Channel")

    wrap_items = [
        ("repeat", "Repeat", "Repeat the image", 0),
        ("clamp", "Clamp", "Extend by repeating edge pixels of the image", 3),
        ("black", "Black", "Clip to image size and use black outside of the image", 1),
        ("white", "White", "Clip to image size and use white outside of the image", 2),
    ]
    wrap: EnumProperty(update=utils_node.force_viewport_update, name="Wrap", items=wrap_items, default="repeat",
                       description="Wrap")

    gamma: FloatProperty(update=utils_node.force_viewport_update, name="Gamma", default=2.2, soft_min=0, soft_max=5,
                         description="Use gamma 2.2 for images with color information (e.g. diffuse maps).\n"
                                     "Use gamma 1.0 for images with other information (e.g. bump maps, "
                                     "roughness maps, metallic maps etc.)")
    brightness: FloatProperty(update=utils_node.force_viewport_update, name="Brightness", default=1,
                              description="Brightness multiplier")

    def update_is_normal_map(self, context):
        color_output = self.outputs["Color"]
        bump_output = self.outputs["Bump"]
        alpha_output = self.outputs["Alpha"]
        was_color_enabled = color_output.enabled

        color_output.enabled = not self.is_normal_map
        alpha_output.enabled = not self.is_normal_map
        bump_output.enabled = self.is_normal_map

        utils_node.copy_links_after_socket_swap(color_output, bump_output, was_color_enabled)
        utils_node.force_viewport_update(self, context)

    is_normal_map: BoolProperty(name="Normalmap", default=False, update=update_is_normal_map,
                                description=NORMAL_MAP_DESC)
    normal_map_scale: FloatProperty(update=utils_node.force_viewport_update, 
                                    name="Height", default=1, min=0, soft_max=5,
                                    description=NORMAL_SCALE_DESC)
    normal_map_orientation_items = [
        ("opengl", "OpenGL", "Select if the image is a left-handed normal map", 0),
        ("directx", "DirectX", "Select if the image is a right-handed normal map (inverted green channel)", 1),
    ]
    normal_map_orientation: EnumProperty(update=utils_node.force_viewport_update, name="Orientation", 
                                         description="Normal Map Orientation",
                                         items=normal_map_orientation_items, default="opengl")

    show_thumbnail: BoolProperty(name="", default=True, description="Show thumbnail")
    
    projection_items = [
        ("flat", "Flat", "Project the image using the UV coordinates", 0),
        ("box", "Box", "Project the image using triplanar box mapping in object space with soft blending between sides", 1),
    ]
    projection: EnumProperty(name="Projection", items=projection_items, default="flat",
                             description="Projection", 
                             update=utils_node.force_viewport_update)
    
    randomized_tiling: BoolProperty(name="Randomized Tiling", default=False,
                                    description="Use histogram-preserving blending to make repetitions irregular",
                                    update=utils_node.force_viewport_update)
        
    filter_items = [
        ("linear", "Linear", "Linear interpolation", 0),
        ("nearest", "Nearest", "Nearest Neighbor interpolation", 1),
    ]
    filter: EnumProperty(name="Interpolation", items=filter_items, default="linear",
                                    description="Interpolation",
                                    update=utils_node.force_viewport_update)
        
    def init(self, context):
        self.show_thumbnail = utils.get_addon_preferences(bpy.context).image_node_thumb_default

        self.add_input("LuxCoreSocketMapping2D", "2D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Alpha")
        self.outputs.new("LuxCoreSocketBump", "Bump")
        self.outputs["Bump"].enabled = False

    def draw_label(self):
        if self.image:
            return self.image.name
        else:
            return self.bl_label

    def draw_buttons(self, context, layout):
        if self.show_thumbnail:
            layout.template_ID_preview(self, "image", open="image.open")
        else:
            layout.template_ID(self, "image", open="image.open")

        col = layout.column()
        col.active = self.image is not None

        row = col.row()
        row.prop(self, "is_normal_map")
        row.prop(self, "show_thumbnail", icon=icons.IMAGE)

        if self.is_normal_map:
            col.prop(self, "normal_map_scale")
            col.prop(self, "normal_map_orientation", text="")
        else:
            col.prop(self, "gamma")
            col.prop(self, "brightness")
            col.prop(self, "channel", text="")

        col.prop(self, "filter", text="")
        col.prop(self, "projection", text="")
        col.prop(self, "wrap", text="")
        if self.wrap == "repeat":
            col.prop(self, "randomized_tiling")
            
        if self.image:
            col.prop(self.image, "source", text="")

            if self.image.source in {"MOVIE", "TILED"}:
                col.label(text="Unsupported Source!", icon=icons.ERROR)

        self.image_user.draw(col, context.scene)
        
        if (not self.inputs["2D Mapping"].is_linked and self.projection == "flat" 
                and context.object and not utils_node.has_valid_uv_map(context.object)):
            col.label(text="No UVs, use box projection!", icon=icons.WARNING)

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        if self.image is None:
            if self.is_normal_map:
                return [0.5, 0.5, 1.0]
            else:
                return [0, 0, 0]

        if self.image.source == "SEQUENCE":
            frame_change_pre.have_to_check_node_trees = True

        try:
            filepath = ImageExporter.export(self.image, self.image_user, exporter.scene)
        except OSError as error:
            msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
            LuxCoreErrorLog.add_warning(msg)
            return [1, 0, 1]

        definitions = {
            "type": "imagemap",
            "file": filepath,
            "wrap": self.wrap,
            "randomizedtiling.enable": self.wrap == "repeat" and self.randomized_tiling,
            "filter": self.filter,
        }
        definitions.update(self.inputs["2D Mapping"].export(exporter, depsgraph, props))

        if self.is_normal_map:
            definitions.update({
                "channel": "rgb" if self.normal_map_orientation == "opengl" else "directx2opengl_normalmap",
                "gamma": 1,
                "gain": 1,
            })
        else:
            definitions.update({
                "channel": "alpha" if output_socket == self.outputs["Alpha"] else self.channel,
                "gamma": self.gamma,
                "gain": self.brightness,
            })

        luxcore_name = self.create_props(props, definitions, luxcore_name)
        
        if self.projection == "box":
            tex_name = luxcore_name + "_triplanar"
            helper_prefix = "scene.textures." + tex_name + "."
            helper_defs = {
                "type": "triplanar",
                "texture1": luxcore_name,
                "texture2": luxcore_name,
                "texture3": luxcore_name,
                "mapping.type": "localmapping3d",
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))
            luxcore_name = tex_name

        if self.is_normal_map:
            tex_name = luxcore_name + "_normalmap"
            helper_prefix = "scene.textures." + tex_name + "."
            helper_defs = {
                "type": "normalmap",
                "texture": luxcore_name,
                "scale": self.normal_map_scale,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))
            luxcore_name = tex_name
        
        return luxcore_name

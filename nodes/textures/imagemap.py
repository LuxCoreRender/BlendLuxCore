import bpy
from bpy.props import (
    PointerProperty, EnumProperty,
    BoolProperty, FloatProperty,
)
from .. import LuxCoreNodeTexture
from ...export.image import ImageExporter
from ...properties.image_user import LuxCoreImageUser
from ... import utils
from ...utils import node as utils_node
from ...utils import ui as utils_ui


NORMAL_MAP_DESC = (
    "Enable if this image is a normal map. Only tangent space maps (the most common "
    "normal maps) are supported. Brightness and gamma will be set to 1"
)
NORMAL_SCALE_DESC = "Height multiplier, used to adjust the baked-in height of the normal map"


class LuxCoreNodeTexImagemap(LuxCoreNodeTexture):
    bl_label = "Imagemap"
    bl_width_default = 200

    def update_image(self, context):
        self.image_user.update(self.image)
        if self.image:
            # Seems like we still need this.
            # User counting does not work reliably with Python PointerProperty.
            # Sometimes, this node is not counted as user.
            self.image.use_fake_user = True

    image = PointerProperty(name="Image", type=bpy.types.Image, update=update_image)
    image_user = PointerProperty(type=LuxCoreImageUser)

    channel_items = [
        ("default", "Default", "Do not convert the image cannels", 0),
        ("rgb", "RGB", "Use RGB color channels", 1),
        ("red", "Red", "Use only the red color channel", 2),
        ("green", "Green", "Use only the green color channel", 3),
        ("blue", "Blue", "Use only the blue color channel", 4),
        ("alpha", "Alpha", "Use only the alpha channel", 5),
        ("mean", "Mean (Average)", "Greyscale", 6),
        ("colored_mean", "Mean (Luminance)", "Greyscale", 7),
    ]
    channel = EnumProperty(name="Channel", items=channel_items, default="default")

    wrap_items = [
        ("repeat", "Repeat", "", 0),
        ("clamp", "Clamp", "Extend the pixels of the border", 3),
        ("black", "Black", "", 1),
        ("white", "White", "", 2),
    ]
    wrap = EnumProperty(name="Wrap", items=wrap_items, default="repeat")

    gamma = FloatProperty(name="Gamma", default=2.2, soft_min=0, soft_max=5,
                          description="Most LDR images with sRgb colors use gamma 2.2, "
                                      "while most HDR images with linear colors use gamma 1")
    brightness = FloatProperty(name="Brightness", default=1,
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

    is_normal_map = BoolProperty(name="Normalmap", default=False, update=update_is_normal_map,
                                 description=NORMAL_MAP_DESC)
    normal_map_scale = FloatProperty(name="Height", default=1, min=0, soft_max=5,
                                     description=NORMAL_SCALE_DESC)
    normal_map_orientation_items = [
        ("opengl", "OpenGL", "Select if the image is a left-handed normal map", 0),
        ("directx", "DirectX", "Select if the image is a right-handed normal map (inverted green channel)", 1),
    ]
    normal_map_orientation = EnumProperty(name="Orientation", items=normal_map_orientation_items, default="opengl")

    # This function assigns self.image to all faces of all objects using this material
    # and assigns self.image to all image editors that do not have their image pinned.
    def update_set_as_active_uvmap(self, context):
        if not self.set_as_active_uvmap:
            return
        # Reset button to "unclicked"
        self["set_as_active_uvmap"] = False

        if not context.object:
            return
        material = context.object.active_material

        for obj in context.scene.objects:
            for mat_index, slot in enumerate(obj.material_slots):
                if slot.material == material:
                    mesh = obj.data
                    if hasattr(mesh, "uv_textures") and mesh.uv_textures:
                        uv_faces = mesh.uv_textures.active.data
                        polygons = mesh.polygons
                        # Unfortunately the uv_face has no information about the material
                        # that is assigned to the face, so we have to get this information
                        # from the polygons of the mesh
                        for uv_face, polygon in zip(uv_faces, polygons):
                            if polygon.material_index == mat_index:
                                uv_face.image = self.image

        for space in utils_ui.get_all_spaces(context, "IMAGE_EDITOR", "IMAGE_EDITOR"):
            # Assign image in all image editors that do not have pinning enabled
            if not space.use_image_pin:
                space.image = self.image

    # Note: the old "use a property as a button because it is so much simpler" trick
    set_as_active_uvmap = BoolProperty(name="Show in Viewport", default=False,
                                       update=update_set_as_active_uvmap,
                                       description="Show this image map on all objects with this material")

    show_thumbnail = BoolProperty(name="", default=True, description="Show thumbnail")

    def init(self, context):
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
        row = layout.row()
        row.prop(self, "show_thumbnail", icon="IMAGE_COL")
        row.prop(self, "set_as_active_uvmap", toggle=True)
        if self.show_thumbnail:
            layout.template_ID_preview(self, "image", open="image.open")
        else:
            layout.template_ID(self, "image", open="image.open")

        col = layout.column()
        col.active = self.image is not None

        col.prop(self, "is_normal_map")

        if self.is_normal_map:
            col.prop(self, "normal_map_scale")
            col.prop(self, "normal_map_orientation")
        else:
            col.prop(self, "channel")

        col.prop(self, "wrap")

        if not self.is_normal_map:
            col.prop(self, "gamma")
            col.prop(self, "brightness")

        # Info about UV mapping (only show if default is used,
        # when no mapping node is linked)
        if not self.inputs["2D Mapping"].is_linked:
            utils_node.draw_uv_info(context, col)

        self.image_user.draw(col, context.scene)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        if self.image is None:
            if self.is_normal_map:
                return [0.5, 0.5, 1.0]
            else:
                return [0, 0, 0]

        try:
            filepath = ImageExporter.export(self.image, self.image_user, exporter.scene)
        except OSError as error:
            msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
            exporter.scene.luxcore.errorlog.add_warning(msg)
            return [1, 0, 1]

        uvscale, uvrotation, uvdelta = self.inputs["2D Mapping"].export(exporter, props)

        definitions = {
            "type": "imagemap",
            "file": filepath,
            "wrap": self.wrap,
            # Mapping
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": uvscale,
            "mapping.rotation": uvrotation,
            "mapping.uvdelta": uvdelta,
        }

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

        if self.is_normal_map:
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

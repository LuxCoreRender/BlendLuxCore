import bpy
from bpy.props import PointerProperty, EnumProperty, BoolProperty, FloatProperty
from .. import LuxCoreNodeTexture
from ...export.image import ImageExporter
from ...utils import node as utils_node
from ... import utils
from ...utils import ui as utils_ui


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
        row = layout.row()
        row.prop(self, "show_thumbnail", icon="IMAGE_COL")
        row.prop(self, "set_as_active_uvmap", toggle=True)
        if self.show_thumbnail:
            layout.template_ID_preview(self, "image", open="image.open")
        else:
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

    def sub_export(self, exporter, props, luxcore_name=None):
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

        uvscale, uvrotation, uvdelta = self.inputs["2D Mapping"].export(exporter, props)

        definitions = {
            "type": "imagemap",
            "file": filepath,
            "gamma": self.inputs["Gamma"].export(exporter, props),
            "gain": self.inputs["Brightness"].export(exporter, props),
            "channel": self.channel,
            "wrap": self.wrap,
            # Mapping
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": uvscale,
            "mapping.rotation": uvrotation,
            "mapping.uvdelta": uvdelta,
        }

        luxcore_name = self.create_props(props, definitions, luxcore_name)

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

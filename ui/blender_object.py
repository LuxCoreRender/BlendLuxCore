from bl_ui.properties_object import ObjectButtonsPanel
from bpy.types import Panel
import bpy
from .. import utils
from ..ui import icons
from ..ui.icons import icon_manager

class LUXCORE_OBJECT_PT_object(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_context = "object"
    bl_label = "LuxCore Object Settings"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout
        obj = context.object

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        if not utils.is_obj_visible_in_cycles(obj):
            col.label(text="Object made invisible through Cycles settings", icon=icons.INFO)
            col = layout.column()
            col.active = False

        col.prop(obj.luxcore, "id")
        col.prop(obj.luxcore, "visible_to_camera")
        col.prop(obj.luxcore, "exclude_from_render")

        # Motion blur settings
        cam = context.scene.camera
        if cam:
            motion_blur = cam.data.luxcore.motion_blur
            object_blur = motion_blur.enable and motion_blur.object_blur

            if not motion_blur.enable:
                col.label(text="Motion blur disabled in camera settings", icon=icons.INFO)
            elif not motion_blur.object_blur:
                col.label(text="Object blur disabled in camera settings", icon=icons.INFO)
        else:
            col.label(text="No camera in scene", icon=icons.INFO)
            object_blur = False

        sub = col.column(align=True)
        sub.enabled = object_blur
        sub.prop(obj.luxcore, "enable_motion_blur")
        
        # Instancing can cost performance, so inform the user when it happens
        if utils.use_obj_motion_blur(obj, context.scene):
            col.label(text="Object will be exported as instance", icon=icons.INFO)


def compatible_panels():
    panels = [
        # Mesh, etc.
        "DATA_PT_context_mesh",
        "DATA_PT_normals",
        "DATA_PT_normals_auto_smooth",
        "DATA_PT_texture_space",
        "DATA_PT_vertex_groups",
        "DATA_PT_face_maps",
        "DATA_PT_shape_keys",
        "DATA_PT_uv_texture",
        "DATA_PT_vertex_colors",
        "DATA_PT_customdata",
        "DATA_PT_custom_props_mesh",
        "DATA_PT_remesh",
        # Speaker
        "DATA_PT_context_speaker",
        "DATA_PT_speaker",
        "DATA_PT_distance",
        "DATA_PT_cone",
        "DATA_PT_custom_props_speaker",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")

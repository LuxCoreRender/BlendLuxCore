from bl_ui.properties_data_camera import CameraButtonsPanel
from . import bpy
from bpy.types import Panel
from bl_ui.utils import PresetPanel
# from ..utils import ui as utils_ui
from . import icons


class LUXCORE_CAMERA_PT_presets(PresetPanel, Panel):
    bl_label = "Camera Presets"
    preset_subdir = "camera"
    preset_operator = "script.execute_preset"
    preset_add_operator = "camera.preset_add"
    COMPAT_ENGINES = {"LUXCORE"}


class LUXCORE_SAFE_AREAS_PT_presets(PresetPanel, Panel):
    bl_label = "Camera Presets"
    preset_subdir = "safe_areas"
    preset_operator = "script.execute_preset"
    preset_add_operator = "safe_areas.preset_add"
    COMPAT_ENGINES = {"LUXCORE"}


class LUXCORE_CAMERA_PT_lens(CameraButtonsPanel, Panel):
    bl_label = "Lens"
    bl_order = 1
    COMPAT_ENGINES = {"LUXCORE"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False      

        cam = context.camera

        layout.prop(cam, "type")

        col = layout.column(align=True)
        col.separator()

        if cam.type == 'PERSP':
            col = layout.column()
            if cam.lens_unit == 'MILLIMETERS':
                col.prop(cam, "lens")
            elif cam.lens_unit == 'FOV':
                col.prop(cam, "angle")
            col.prop(cam, "lens_unit")

        elif cam.type == 'ORTHO':
            col.prop(cam, "ortho_scale")

        col = layout.column(align=True)
        col.separator()

        sub = col.column(align=True)
        sub.prop(cam, "shift_x", text="Shift X")
        sub.prop(cam, "shift_y", text="Y")

        col.separator()
        col.prop(cam.luxcore, "use_clipping")        
        sub = col.column(align=True)
        sub.enabled = cam.luxcore.use_clipping        
        sub.prop(cam, "clip_start", text="Clip Start")
        sub.prop(cam, "clip_end", text="End")

#TODO: separate class for volume
#TODO: Reactivate when volume code is implemented
##        # Volume
##        layout.prop(cam.luxcore, "auto_volume")
##
##        if not cam.luxcore.auto_volume:
##            layout.label(text="Camera Volume:")
##            utils_ui.template_node_tree(layout, cam.luxcore, "volume", icons.NTREE_VOLUME,
##                                        "LUXCORE_VOLUME_MT_camera_select_volume_node_tree",
##                                        "luxcore.camera_show_volume_node_tree",
##                                        "luxcore.camera_new_volume_node_tree",
##                                        "luxcore.camera_unlink_volume_node_tree")


##class LUXCORE_PT_camera(CameraButtonsPanel, Panel):
##    bl_label = "Camera"
##    bl_order = 2
##    bl_options = {'DEFAULT_CLOSED'}
##    COMPAT_ENGINES = {"LUXCORE"}
##
##    def draw_header_preset(self, _context):
##        LUXCORE_CAMERA_PT_presets.draw_panel_header(self.layout)
##
##    def draw(self, context):
##        layout = self.layout
##
##        cam = context.camera
##
##        layout.use_property_split = True
##
##        col = layout.column()
##        col.prop(cam, "sensor_fit")
##
##        if cam.sensor_fit == 'AUTO':
##            col.prop(cam, "sensor_width", text="Size")
##        else:
##            sub = col.column(align=True)
##            sub.active = cam.sensor_fit == 'HORIZONTAL'
##            sub.prop(cam, "sensor_width", text="Width")
##
##            sub = col.column(align=True)
##            sub.active = cam.sensor_fit == 'VERTICAL'
##            sub.prop(cam, "sensor_height", text="Height")


class LUXCORE_CAMERA_PT_clipping_plane(CameraButtonsPanel, Panel):
    bl_label = "Clipping Plane"
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        self.layout.prop(context.camera.luxcore, "use_clipping_plane", text="")

    def draw(self, context):
        layout = self.layout
        cam = context.camera
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        sub = layout.column(align=True)
        sub.enabled = cam.luxcore.use_clipping_plane
        sub.prop(cam.luxcore, "clipping_plane", text="")


class LUXCORE_CAMERA_PT_depth_of_field(CameraButtonsPanel, Panel):
    bl_label = "Depth of Field"
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        self.layout.prop(context.camera.luxcore, "use_dof", text="")

    def draw(self, context):
        layout = self.layout
        cam = context.camera
        dof_options = cam.dof
        layout.use_property_split = True
        layout.use_property_decorate = False      

        layout.enabled = cam.luxcore.use_dof

        layout.prop(cam.luxcore, "fstop")
        layout.prop(cam.luxcore, "use_autofocus")

        col = layout.column(align=True)
        col.enabled = not cam.luxcore.use_autofocus        
        col.prop(dof_options, "focus_object")
        col = layout.column(align=True)
        col.enabled = (dof_options.focus_object is None and not cam.luxcore.use_autofocus)
        col.prop(dof_options, "focus_distance", text="Distance")


class LUXCORE_CAMERA_PT_dof_aperture(CameraButtonsPanel, Panel):
    bl_label = "Aperture"    
    bl_parent_id = "LUXCORE_CAMERA_PT_depth_of_field"
    COMPAT_ENGINES = {"LUXCORE"}

    @classmethod
    def poll(cls, context):
        return context.camera

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False      

        cam = context.camera
        dof = cam.dof
        layout.enabled = cam.luxcore.use_dof
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        col = flow.column(align=True)
        col.prop(dof, "aperture_fstop")
        col.prop(dof, "aperture_blades")
        col.prop(dof, "aperture_rotation")
        col.prop(dof, "aperture_ratio")


class LUXCORE_CAMERA_PT_camera_display(CameraButtonsPanel, Panel):
    bl_label = "Viewport Display"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 5
    COMPAT_ENGINES = {"LUXCORE"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        cam = context.camera

        col = layout.column(align=True)

        col.separator()

        col.prop(cam, "display_size", text="Size")

        col.separator()

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=False, even_rows=False, align=False)

        col = flow.column()
        col.prop(cam, "show_limits", text="Limits")
        col = flow.column()
        col.prop(cam, "show_mist", text="Mist")
        col = flow.column()
        col.prop(cam, "show_sensor", text="Sensor")
        col = flow.column()
        col.prop(cam, "show_name", text="Name")


class LUXCORE_CAMERA_PT_camera_display_composition_guides(CameraButtonsPanel, Panel):
    bl_label = "Composition Guides"
    bl_parent_id = "LUXCORE_CAMERA_PT_camera_display"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        cam = context.camera

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=False, even_rows=False, align=False)

        col = flow.column()
        col.prop(cam, "show_composition_center")
        col = flow.column()
        col.prop(cam, "show_composition_center_diagonal")
        col = flow.column()
        col.prop(cam, "show_composition_thirds")
        col = flow.column()
        col.prop(cam, "show_composition_golden")
        col = flow.column()
        col.prop(cam, "show_composition_golden_tria_a")
        col = flow.column()
        col.prop(cam, "show_composition_golden_tria_b")
        col = flow.column()
        col.prop(cam, "show_composition_harmony_tri_a")
        col = flow.column()
        col.prop(cam, "show_composition_harmony_tri_b")


class LUXCORE_CAMERA_PT_camera_display_passepartout(CameraButtonsPanel, Panel):
    bl_label = "Passepartout"
    bl_parent_id = "LUXCORE_CAMERA_PT_camera_display"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        cam = context.camera

        self.layout.prop(cam, "show_passepartout", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        cam = context.camera

        layout.active = cam.show_passepartout
        layout.prop(cam, "passepartout_alpha", text="Opacity", slider=True)

class LUXCORE_CAMERA_PT_camera_safe_areas(CameraButtonsPanel, Panel):
    bl_label = "Safe Areas"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 6
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        cam = context.camera

        self.layout.prop(cam, "show_safe_areas", text="")

    def draw_header_preset(self, _context):
        LUXCORE_SAFE_AREAS_PT_presets.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        safe_data = context.scene.safe_areas
        camera = context.camera

        layout.use_property_split = True

        layout.active = camera.show_safe_areas

        col = layout.column()

        sub = col.column()
        sub.prop(safe_data, "title", slider=True)
        sub.prop(safe_data, "action", slider=True)


class LUXCORE_CAMERA_PT_camera_safe_areas_center_cut(CameraButtonsPanel, Panel):
    bl_label = "Center-Cut Safe Areas"
    bl_parent_id = "LUXCORE_CAMERA_PT_camera_safe_areas"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        cam = context.camera

        layout = self.layout
        layout.active = cam.show_safe_areas
        layout.prop(cam, "show_safe_center", text="")

    def draw(self, context):
        layout = self.layout
        safe_data = context.scene.safe_areas
        camera = context.camera

        layout.use_property_split = True

        layout.active = camera.show_safe_areas and camera.show_safe_center

        col = layout.column()
        col.prop(safe_data, "title_center", slider=True)


class LUXCORE_CAMERA_PT_motion_blur(CameraButtonsPanel, Panel):
    bl_label = "Motion Blur"
    bl_order = 7
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        self.layout.prop(context.camera.luxcore.motion_blur, "enable", text="")

    def draw(self, context):
        layout = self.layout
        cam = context.camera
        motion_blur = cam.luxcore.motion_blur
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.enabled = motion_blur.enable

        col = layout.column(align=True)
        col.prop(motion_blur, "object_blur")
        col.prop(motion_blur, "camera_blur")

        col = layout.column(align=True)
        col.prop(motion_blur, "shutter")
        col.prop(motion_blur, "steps")

        if motion_blur.camera_blur:
            layout.label(text="Camera blur is only visible in final render", icon=icons.INFO)
            

class LUXCORE_CAMERA_PT_image_pipeline(CameraButtonsPanel, Panel):
    bl_label = "Image pipeline"
    bl_order = 8
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}
##
##    def draw_plugin_box(self, settings):
##        col = self.layout.column(align=True)
##        # Header
##        icon = "RESTRICT_RENDER_OFF" if settings.enabled else "RESTRICT_RENDER_ON"
##        col.prop(settings, "enabled", icon=icon, emboss=True)
##        # Body
##        if settings.enabled:
##            return col.box()
##        else:
##            return None
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False      
        cam = context.camera
        pipeline = cam.luxcore.imagepipeline

        # General settings
        layout.prop(pipeline, "transparent_film")
        layout.prop(context.scene.luxcore.config, "film_opencl_enable")
        if context.scene.luxcore.config.film_opencl_enable:
            layout.prop(context.scene.luxcore.config, "film_opencl_device", text="")

        # Tonemapper settings
        tonemapper = pipeline.tonemapper
##        box = self.draw_plugin_box(tonemapper)
##        if box:
##            row = box.row()
##            row.prop(tonemapper, "type", expand=True)
##
##            if tonemapper.type == "TONEMAP_LINEAR":
##                row = box.row()
##                row.prop(tonemapper, "linear_scale")
##                row.prop(tonemapper, "use_autolinear")
##            elif tonemapper.type == "TONEMAP_LUXLINEAR":
##                row = box.row(align=True)
##                row.prop(tonemapper, "fstop")
##                row.prop(tonemapper, "exposure")
##                row.prop(tonemapper, "sensitivity")
##            elif tonemapper.type == "TONEMAP_REINHARD02":
##                row = box.row(align=True)
##                row.prop(tonemapper, "reinhard_prescale")
##                row.prop(tonemapper, "reinhard_postscale")
##                row.prop(tonemapper, "reinhard_burn")
##
##            if len(context.scene.render.layers) > 1 and tonemapper.is_automatic():
##                name = "Auto" if tonemapper.type == "TONEMAP_LINEAR" else "Reinhard"
##                msg = name + " and multiple renderlayers will cause brightness difference!"
##                box.label(text=msg, icon=icons.WARNING)
##
##        if context.scene.luxcore.viewport.denoise:
##            layout.label(text="Plugins below disabled in viewport because of viewport denoising", icon=icons.INFO)
##
##        # Bloom settings
##        bloom = pipeline.bloom
##        box = self.draw_plugin_box(bloom)
##        if box:
##            row = box.row()
##            row.prop(bloom, "radius")
##            row.prop(bloom, "weight")
##
##        mist = pipeline.mist
##        box = self.draw_plugin_box(mist)
##        if box:
##            col = box.column(align=True)
##            col.scale_y = 0.8
##            col.label(text="Note: the mist is not anti-aliased.", icon=icons.WARNING)
##            col.label(text="This causes jagged edges if the effect is too strong.")
##            row = box.row()
##            row.prop(mist, "color", text="")
##            row.prop(mist, "amount", slider=True)
##            row = box.row(align=True)
##            row.prop(mist, "start_distance")
##            row.prop(mist, "end_distance")
##            box.prop(mist, "exclude_background")
##
##        vignetting = pipeline.vignetting
##        box = self.draw_plugin_box(vignetting)
##        if box:
##            box.prop(vignetting, "scale", slider=True)
##
##        coloraberration = pipeline.coloraberration
##        box = self.draw_plugin_box(coloraberration)
##        if box:
##            box.prop(coloraberration, "amount", slider=True)
##
##        camera_response_func = pipeline.camera_response_func
##        box = self.draw_plugin_box(camera_response_func)
##        if box:
##            row = box.row()
##            row.prop(camera_response_func, "type", expand=True)
##
##            if camera_response_func.type == "PRESET":
##                selected = camera_response_func.preset
##                label = selected.replace("_", " ") if selected else "Select Preset"
##                box.operator("luxcore.select_crf", text=label)
##            else:
##                box.prop(camera_response_func, "file")
##
##        contour_lines = pipeline.contour_lines
##        box = self.draw_plugin_box(contour_lines)
##        if box:
##            row = box.row(align=True)
##            row.prop(contour_lines, "scale")
##            row.prop(contour_lines, "contour_range")
##            row = box.row(align=True)
##            row.prop(contour_lines, "steps")
##            row.prop(contour_lines, "zero_grid_size")


class LUXCORE_CAMERA_PT_background_image(CameraButtonsPanel, Panel):
    bl_label = "Background Image"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    COMPAT_ENGINES = {"LUXCORE"}    
    
    def draw_header(self, context):
        cam = context.camera
        pipeline = cam.luxcore.imagepipeline        
        self.layout.prop(pipeline.backgroundimage, "enabled", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False      

        cam = context.camera
        pipeline = cam.luxcore.imagepipeline
        backgroundimage = pipeline.backgroundimage

        col = layout.column(align=True)
        col.enabled = backgroundimage.enabled
        col.template_ID(backgroundimage, "image", open="image.open")
        col.prop(backgroundimage, "gamma")
        backgroundimage.image_user.draw(col, context.scene)
        col.prop(backgroundimage, "storage")


def compatible_panels():
     panels = [
        "DATA_PT_context_camera",
        "DATA_PT_camera_stereoscopy",
        #"DATA_PT_camera",
        #"DATA_PT_camera_background_image",
        #"DATA_PT_camera_display",
        #"DATA_PT_camera_display_composition_guides",
        #"DATA_PT_camera_display_passepartout",
        #"DATA_PT_camera_safe_areas",
        #"DATA_PT_camera_safe_areas_center_cut",
        "DATA_PT_custom_props_camera",
     ]
     types = bpy.types
     return [getattr(types, p) for p in panels if hasattr(types, p)]

def register():
    for panel in compatible_panels():        
        panel.COMPAT_ENGINES.add("LUXCORE")            


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")

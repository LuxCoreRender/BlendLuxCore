from bl_ui.properties_data_camera import CameraButtonsPanel
import bpy
from bpy.types import Panel
from bl_ui.utils import PresetPanel
from ..utils import ui as utils_ui
from . import icons
from ..ui.icons import icon_manager


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
        sub.active = cam.luxcore.use_clipping
        sub.prop(cam, "clip_start", text="Clip Start")
        sub.prop(cam, "clip_end", text="End")


class LUXCORE_CAMERA_PT_clipping_plane(CameraButtonsPanel, Panel):
    bl_label = "Clipping Plane"
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))
        col = layout.column(align=True)
        col.prop(context.camera.luxcore, "use_clipping_plane", text="")

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
        layout = self.layout
        layout.prop(context.camera.dof, "use_dof", text="")


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        
        cam = context.camera

        layout.active = cam.dof.use_dof

        layout.prop(cam.dof, "aperture_fstop")
        layout.prop(cam.luxcore, "use_autofocus")

        col = layout.column(align=True)
        col.active = not cam.luxcore.use_autofocus        
        col.prop(cam.dof, "focus_object")
        col = layout.column(align=True)
        col.active = (cam.dof.focus_object is None and not cam.luxcore.use_autofocus)
        col.prop(cam.dof, "focus_distance", text="Distance")


class LUXCORE_CAMERA_PT_bokeh(CameraButtonsPanel, Panel):
    bl_label = "Non-Uniform Bokeh"
    bl_parent_id = "LUXCORE_CAMERA_PT_depth_of_field"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}
    
    def draw_header(self, context):
        layout = self.layout
        layout.prop(context.camera.luxcore.bokeh, "non_uniform", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        
        cam = context.camera
        bokeh = cam.luxcore.bokeh
        
        layout.active = bokeh.non_uniform

        layout.prop(bokeh, "blades")
        layout.prop(bokeh, "anisotropy")
        
        col = layout.column()
        col.prop(bokeh, "distribution")
        if bokeh.distribution in {"EXPONENTIAL", "INVERSEEXPONENTIAL"}:
            col.prop(bokeh, "power")
        elif bokeh.distribution == "CUSTOM":
            col.template_ID(bokeh, "image", open="image.open")
            bokeh.image_user.draw(col, context.scene)


class LUXCORE_CAMERA_PT_motion_blur(CameraButtonsPanel, Panel):
    bl_label = "Motion Blur"
    bl_order = 7
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))
        col = layout.column(align=True)
        col.prop(context.camera.luxcore.motion_blur, "enable", text="")

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
    bl_label = "Image Pipeline"
    bl_order = 8
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        pipeline = context.camera.luxcore.imagepipeline

        layout.prop(pipeline, "transparent_film")
            

class LUXCORE_CAMERA_PT_image_pipeline_tonemapper(CameraButtonsPanel, Panel):
    bl_label = "Tonemapper"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    
    COMPAT_ENGINES = {"LUXCORE"}    
    
    def draw_header(self, context):
        layout = self.layout
        pipeline = context.camera.luxcore.imagepipeline
        layout.prop(pipeline.tonemapper, "enabled", text="")


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        pipeline = context.camera.luxcore.imagepipeline
        tonemapper = pipeline.tonemapper
        layout.enabled = tonemapper.enabled
        
        layout.prop(tonemapper, "type", expand=False)

        if tonemapper.type == "TONEMAP_LINEAR":
            col = layout.column(align=True)            
            col.prop(tonemapper, "linear_scale")
            col.prop(tonemapper, "use_autolinear")
        elif tonemapper.type == "TONEMAP_LUXLINEAR":
            col = layout.column(align=True)            
            col.prop(tonemapper, "fstop")
            col.prop(tonemapper, "exposure")
            col.prop(tonemapper, "sensitivity")
        elif tonemapper.type == "TONEMAP_REINHARD02":
            col = layout.column(align=True)            
            col.prop(tonemapper, "reinhard_prescale")
            col.prop(tonemapper, "reinhard_postscale")
            col.prop(tonemapper, "reinhard_burn")

        if len(context.scene.view_layers) > 1 and tonemapper.is_automatic():
            name = "Auto" if tonemapper.type == "TONEMAP_LINEAR" else "Reinhard"
            msg = name + " and multiple renderlayers will cause brightness difference!"
            col = layout.column(align=True)
            col.label(text=msg, icon=icons.WARNING)


class LUXCORE_CAMERA_PT_image_pipeline_bloom(CameraButtonsPanel, Panel):
    bl_label = "Bloom"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}    
    
    def draw_header(self, context):        
        pipeline = context.camera.luxcore.imagepipeline        
        self.layout.prop(pipeline.bloom, "enabled", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        pipeline = context.camera.luxcore.imagepipeline
        bloom = pipeline.bloom
        layout.enabled = bloom.enabled

        layout.prop(bloom, "radius")
        layout.prop(bloom, "weight")


class LUXCORE_CAMERA_PT_image_pipeline_mist(CameraButtonsPanel, Panel):
    bl_label = "Mist"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}    
    
    def draw_header(self, context):        
        pipeline = context.camera.luxcore.imagepipeline        
        self.layout.prop(pipeline.mist, "enabled", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        pipeline = context.camera.luxcore.imagepipeline
        mist = pipeline.mist
        layout.enabled = mist.enabled

        col = layout.column(align=True)
        col.scale_y = 0.8
        col.label(text="Note: the mist is not anti-aliased.", icon=icons.WARNING)
        col.label(text="This causes jagged edges if the effect is too strong.")

        layout.prop(mist, "color")
        layout.prop(mist, "amount", slider=True)
        
        col = layout.column(align=True)
        col.prop(mist, "start_distance")
        col.prop(mist, "end_distance")
        layout.prop(mist, "exclude_background")


class LUXCORE_CAMERA_PT_image_pipeline_vignetting(CameraButtonsPanel, Panel):
    bl_label = "Vignetting"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}    
    
    def draw_header(self, context):        
        pipeline = context.camera.luxcore.imagepipeline        
        self.layout.prop(pipeline.vignetting, "enabled", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        pipeline = context.camera.luxcore.imagepipeline
        vignetting = pipeline.vignetting
        layout.enabled = vignetting.enabled

        layout.prop(vignetting, "scale", slider=True)


class LUXCORE_CAMERA_PT_image_pipeline_color_aberration(CameraButtonsPanel, Panel):
    bl_label = "Color Aberration"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}    
    
    def draw_header(self, context):        
        pipeline = context.camera.luxcore.imagepipeline        
        self.layout.prop(pipeline.coloraberration, "enabled", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        pipeline = context.camera.luxcore.imagepipeline
        coloraberration = pipeline.coloraberration
        layout.enabled = coloraberration.enabled

        if context.scene.luxcore.viewport.get_denoiser(context) == "OIDN":
            self.layout.label(text="Disabled in viewport because of viewport denoising", icon=icons.INFO)

        layout.prop(coloraberration, "uniform")
        if coloraberration.uniform:
            layout.prop(coloraberration, "amount", slider=True)
        else:
            col = layout.column(align=True)
            col.prop(coloraberration, "amount", slider=True, text="Strength (X)")
            col.prop(coloraberration, "amount_y", slider=True)


class LUXCORE_CAMERA_PT_image_pipeline_background_image(CameraButtonsPanel, Panel):
    bl_label = "Background Image"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}    
    
    def draw_header(self, context):        
        pipeline = context.camera.luxcore.imagepipeline        
        self.layout.prop(pipeline.backgroundimage, "enabled", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        pipeline = context.camera.luxcore.imagepipeline
        backgroundimage = pipeline.backgroundimage
        layout.enabled = backgroundimage.enabled

        col = layout.column(align=True)
        col.enabled = backgroundimage.enabled
        col.template_ID(backgroundimage, "image", open="image.open")
        col.prop(backgroundimage, "gamma")
        backgroundimage.image_user.draw(col, context.scene)
        col.prop(backgroundimage, "storage")


class LUXCORE_CAMERA_PT_image_pipeline_white_balance(CameraButtonsPanel, Panel):
    bl_label = "White Balance"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        pipeline = context.camera.luxcore.imagepipeline
        self.layout.prop(pipeline.white_balance, "enabled", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        pipeline = context.camera.luxcore.imagepipeline
        white_balance = pipeline.white_balance
        layout.enabled = white_balance.enabled

        layout.prop(white_balance, "temperature", slider=True)
        layout.prop(white_balance, "reverse")


class LUXCORE_CAMERA_PT_image_pipeline_camera_response_function(CameraButtonsPanel, Panel):
    bl_label = "Analog Film Simulation"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}    
    
    def draw_header(self, context):        
        pipeline = context.camera.luxcore.imagepipeline        
        self.layout.prop(pipeline.camera_response_func, "enabled", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        pipeline = context.camera.luxcore.imagepipeline
        camera_response_func = pipeline.camera_response_func
        layout.enabled = camera_response_func.enabled

        layout.prop(camera_response_func, "type", expand=True)

        if camera_response_func.type == "PRESET":
            selected = camera_response_func.preset
            label = selected.replace("_", " ") if selected else "Select Preset"
            layout.operator("luxcore.select_crf", text=label)
        else:
            layout.prop(camera_response_func, "file")


class LUXCORE_CAMERA_PT_image_pipeline_color_LUT(CameraButtonsPanel, Panel):
    bl_label = "LUT"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        pipeline = context.camera.luxcore.imagepipeline
        self.layout.prop(pipeline.color_LUT, "enabled", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        pipeline = context.camera.luxcore.imagepipeline
        color_LUT = pipeline.color_LUT
        layout.enabled = color_LUT.enabled

        layout.prop(color_LUT, "input_colorspace")
        view_settings = context.scene.view_settings
        if (color_LUT.input_colorspace == "SRGB_GAMMA_CORRECTED"
                and (view_settings.view_transform != "Raw" or view_settings.gamma != 1)):
            layout.label(text="Needs Raw view transform and gamma = 1", icon=icons.WARNING)
            layout.operator("luxcore.set_raw_view_transform")

        layout.prop(color_LUT, "file")
        layout.prop(color_LUT, "strength")


class LUXCORE_CAMERA_PT_image_pipeline_contour_lines(CameraButtonsPanel, Panel):
    bl_label = "Irradiance Contour Lines"
    bl_parent_id = "LUXCORE_CAMERA_PT_image_pipeline"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {"LUXCORE"}    
    
    def draw_header(self, context):        
        pipeline = context.camera.luxcore.imagepipeline        
        self.layout.prop(pipeline.contour_lines, "enabled", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        pipeline = context.camera.luxcore.imagepipeline
        contour_lines = pipeline.contour_lines
        layout.enabled = contour_lines.enabled

        if context.scene.luxcore.viewport.get_denoiser(context) == "OIDN":
            self.layout.label(text="Disabled in viewport because of viewport denoising", icon=icons.INFO)

        layout.prop(contour_lines, "scale")
        layout.prop(contour_lines, "contour_range")
        layout.prop(contour_lines, "steps")
        layout.prop(contour_lines, "zero_grid_size")


class LUXCORE_CAMERA_PT_volume(CameraButtonsPanel, Panel):
    bl_label = "Exterior Volume"
    bl_order = 8
    COMPAT_ENGINES = {"LUXCORE"}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE" and context.camera

    def draw_header(self, contxt):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        cam = context.camera

        layout.prop(cam.luxcore, "auto_volume")

        if not cam.luxcore.auto_volume:
            utils_ui.template_node_tree(layout, cam.luxcore, "volume", icons.NTREE_VOLUME,
                                        "LUXCORE_VOLUME_MT_camera_select_volume_node_tree",
                                        "luxcore.camera_show_volume_node_tree",
                                        "luxcore.camera_new_volume_node_tree",
                                        "luxcore.camera_unlink_volume_node_tree")


def compatible_panels():
    panels = [
        "DATA_PT_context_camera",
        "DATA_PT_camera",
        "DATA_PT_camera_background_image",
        "DATA_PT_custom_props_camera",
        "DATA_PT_camera_display",
        "DATA_PT_camera_display_composition_guides",
        "DATA_PT_camera_display_passepartout",
        "DATA_PT_camera_safe_areas",
        "DATA_PT_camera_safe_areas_center_cut",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")

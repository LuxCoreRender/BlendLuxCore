from bl_ui.properties_data_camera import CameraButtonsPanel
from bpy.types import Panel
from ..utils import ui as utils_ui
from . import icons


class LUXCORE_CAMERA_PT_lens(CameraButtonsPanel, Panel):
    bl_label = "Lens"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_options = {"HIDE_HEADER"}

    def draw(self, context):
        layout = self.layout

        cam = context.camera
        obj = context.object
        space = context.space_data

        split = layout.split(percentage=0.65)
        if obj:
            split.template_ID(obj, "data")
            split.separator()
        elif cam:
            split.template_ID(space, "pin_id")
            split.separator()
        layout.separator()

        layout.row().prop(cam, "type", expand=True)

        split = layout.split()

        col = split.column()
        if cam.type == "PERSP":
            row = col.row()
            if cam.lens_unit == "MILLIMETERS":
                row.prop(cam, "lens")
            elif cam.lens_unit == "FOV":
                row.prop(cam, "angle")
            row.prop(cam, "lens_unit", text="")

        elif cam.type == "ORTHO":
            col.prop(cam, "ortho_scale")

        split = layout.split()

        col = split.column(align=True)
        col.label(text="Shift:")
        col.prop(cam, "shift_x", text="X")
        col.prop(cam, "shift_y", text="Y")

        # In LuxCore, clipping is optional
        col = split.column(align=True)
        col.prop(cam.luxcore, "use_clipping")
        sub = col.column(align=True)
        sub.active = cam.luxcore.use_clipping
        sub.prop(cam, "clip_start", text="Start")
        sub.prop(cam, "clip_end", text="End")

        row = layout.row(align=True)
        row.prop(cam.luxcore, "use_clipping_plane")
        sub = row.row(align=True)
        sub.active = cam.luxcore.use_clipping_plane
        sub.prop(cam.luxcore, "clipping_plane", text="")

        # Volume
        layout.prop(cam.luxcore, "auto_volume")

        if not cam.luxcore.auto_volume:
            layout.label("Camera Volume:")
            utils_ui.template_node_tree(layout, cam.luxcore, "volume", icons.NTREE_VOLUME,
                                        "LUXCORE_VOLUME_MT_camera_select_volume_node_tree",
                                        "luxcore.camera_show_volume_node_tree",
                                        "luxcore.camera_new_volume_node_tree",
                                        "luxcore.camera_unlink_volume_node_tree")


class LUXCORE_CAMERA_PT_imagepipeline(CameraButtonsPanel, Panel):
    bl_label = "LuxCore Imagepipeline"
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_plugin_box(self, settings):
        col = self.layout.column(align=True)
        # Header
        icon = "RESTRICT_RENDER_OFF" if settings.enabled else "RESTRICT_RENDER_ON"
        col.prop(settings, "enabled", icon=icon, emboss=True)
        # Body
        if settings.enabled:
            return col.box()
        else:
            return None

    def draw(self, context):
        layout = self.layout
        cam = context.camera
        pipeline = cam.luxcore.imagepipeline

        # General settings
        layout.prop(pipeline, "transparent_film")
        row = layout.row()
        row.prop(context.scene.luxcore.config, "film_opencl_enable")
        if context.scene.luxcore.config.film_opencl_enable:
            row.prop(context.scene.luxcore.config, "film_opencl_device", text="")

        # Tonemapper settings
        tonemapper = pipeline.tonemapper
        box = self.draw_plugin_box(tonemapper)
        if box:
            row = box.row()
            row.prop(tonemapper, "type", expand=True)

            if tonemapper.type == "TONEMAP_LINEAR":
                row = box.row()
                row.prop(tonemapper, "linear_scale")
                row.prop(tonemapper, "use_autolinear")
            elif tonemapper.type == "TONEMAP_LUXLINEAR":
                row = box.row(align=True)
                row.prop(tonemapper, "fstop")
                row.prop(tonemapper, "exposure")
                row.prop(tonemapper, "sensitivity")
            elif tonemapper.type == "TONEMAP_REINHARD02":
                row = box.row(align=True)
                row.prop(tonemapper, "reinhard_prescale")
                row.prop(tonemapper, "reinhard_postscale")
                row.prop(tonemapper, "reinhard_burn")

            if len(context.scene.render.layers) > 1 and tonemapper.is_automatic():
                name = "Auto" if tonemapper.type == "TONEMAP_LINEAR" else "Reinhard"
                msg = name + " and multiple renderlayers will cause brightness difference!"
                box.label(msg, icon=icons.WARNING)

        # Bloom settings
        bloom = pipeline.bloom
        box = self.draw_plugin_box(bloom)
        if box:
            row = box.row()
            row.prop(bloom, "radius")
            row.prop(bloom, "weight")

        mist = pipeline.mist
        box = self.draw_plugin_box(mist)
        if box:
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label("Note: the mist is not anti-aliased.", icon=icons.WARNING)
            col.label("This causes jagged edges if the effect is too strong.")
            row = box.row()
            row.prop(mist, "color", text="")
            row.prop(mist, "amount", slider=True)
            row = box.row(align=True)
            row.prop(mist, "start_distance")
            row.prop(mist, "end_distance")
            box.prop(mist, "exclude_background")

        vignetting = pipeline.vignetting
        box = self.draw_plugin_box(vignetting)
        if box:
            box.prop(vignetting, "scale", slider=True)

        coloraberration = pipeline.coloraberration
        box = self.draw_plugin_box(coloraberration)
        if box:
            box.prop(coloraberration, "amount", slider=True)

        backgroundimage = pipeline.backgroundimage
        box = self.draw_plugin_box(backgroundimage)
        if box:
            box.template_ID(backgroundimage, "image", open="image.open")
            box.prop(backgroundimage, "gamma")
            backgroundimage.image_user.draw(box, context.scene)
            box.prop(backgroundimage, "storage")

        camera_response_func = pipeline.camera_response_func
        box = self.draw_plugin_box(camera_response_func)
        if box:
            row = box.row()
            row.prop(camera_response_func, "type", expand=True)

            if camera_response_func.type == "PRESET":
                selected = camera_response_func.preset
                label = selected.replace("_", " ") if selected else "Select Preset"
                box.operator("luxcore.select_crf", text=label)
            else:
                box.prop(camera_response_func, "file")

        contour_lines = pipeline.contour_lines
        box = self.draw_plugin_box(contour_lines)
        if box:
            row = box.row(align=True)
            row.prop(contour_lines, "scale")
            row.prop(contour_lines, "contour_range")
            row = box.row(align=True)
            row.prop(contour_lines, "steps")
            row.prop(contour_lines, "zero_grid_size")


class LUXCORE_CAMERA_PT_depth_of_field(CameraButtonsPanel, Panel):
    bl_label = "Depth of Field"
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        self.layout.prop(context.camera.luxcore, "use_dof", text="")

    def draw(self, context):
        layout = self.layout
        cam = context.camera
        dof_options = cam.gpu_dof
        layout.active = cam.luxcore.use_dof

        layout.prop(cam.luxcore, "fstop")
        layout.prop(cam.luxcore, "use_autofocus")

        split = layout.split()

        col = split.column()
        col.active = not cam.luxcore.use_autofocus
        col.label(text="Focus:")
        col.prop(cam, "dof_object", text="")
        sub = col.column()
        sub.active = (cam.dof_object is None)
        sub.prop(cam, "dof_distance", text="Distance")

        hq_support = dof_options.is_hq_supported
        col = split.column(align=True)
        col.label("Viewport:")
        sub = col.column()
        sub.active = hq_support
        sub.prop(dof_options, "use_high_quality")
        col.prop(dof_options, "fstop")
        if dof_options.use_high_quality and hq_support:
            col.prop(dof_options, "blades")


class LUXCORE_CAMERA_PT_motion_blur(CameraButtonsPanel, Panel):
    bl_label = "Motion Blur"
    COMPAT_ENGINES = {"LUXCORE"}

    def draw_header(self, context):
        self.layout.prop(context.camera.luxcore.motion_blur, "enable", text="")

    def draw(self, context):
        layout = self.layout
        cam = context.camera
        motion_blur = cam.luxcore.motion_blur
        layout.active = motion_blur.enable

        split = layout.split()

        col = split.column(align=True)
        col.prop(motion_blur, "object_blur")
        col.prop(motion_blur, "camera_blur")

        col = split.column(align=True)
        col.prop(motion_blur, "shutter")
        col.prop(motion_blur, "steps")

        if motion_blur.camera_blur:
            layout.label("Camera blur is only visible in final render", icon=icons.INFO)

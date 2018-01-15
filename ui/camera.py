from bl_ui.properties_data_camera import CameraButtonsPanel
from bpy.types import Panel


class LuxCoreLens(CameraButtonsPanel, Panel):
    bl_label = "Lens"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_options = {"HIDE_HEADER"}

    def draw(self, context):
        layout = self.layout

        cam = context.camera

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


class LuxCoreDepthOfField(CameraButtonsPanel, Panel):
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


class LuxCoreMotionBlur(CameraButtonsPanel, Panel):
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

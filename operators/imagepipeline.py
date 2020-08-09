import bpy
from bpy.props import EnumProperty, StringProperty, IntProperty

# Valid CRF preset names (case sensitive):
# See lux/core/cameraresponse.cpp to keep this up to date
crf_preset_names = [
    s.strip() for s in
    """Advantix_100CD
    Advantix_200CD
    Advantix_400CD
    Agfachrome_ctpecisa_200CD
    Agfachrome_ctprecisa_100CD
    Agfachrome_rsx2_050CD
    Agfachrome_rsx2_100CD
    Agfachrome_rsx2_200CD
    Agfacolor_futura_100CD
    Agfacolor_futura_200CD
    Agfacolor_futura_400CD
    Agfacolor_futuraII_100CD
    Agfacolor_futuraII_200CD
    Agfacolor_futuraII_400CD
    Agfacolor_hdc_100_plusCD
    Agfacolor_hdc_200_plusCD
    Agfacolor_hdc_400_plusCD
    Agfacolor_optimaII_100CD
    Agfacolor_optimaII_200CD
    Agfacolor_ultra_050_CD
    Agfacolor_vista_100CD
    Agfacolor_vista_200CD
    Agfacolor_vista_400CD
    Agfacolor_vista_800CD
    Ektachrome_100_plusCD
    Ektachrome_100CD
    Ektachrome_320TCD
    Ektachrome_400XCD
    Ektachrome_64CD
    Ektachrome_64TCD
    Ektachrome_E100SCD
    F125CD
    F250CD
    F400CD
    FCICD
    Gold_100CD
    Gold_200CD
    Kodachrome_200CD
    Kodachrome_25CD
    Kodachrome_64CD
    Max_Zoom_800CD
    Portra_100TCD
    Portra_160NCCD
    Portra_160VCCD
    Portra_400NCCD
    Portra_400VCCD
    Portra_800CD""".splitlines()
]


class LUXCORE_OT_select_crf(bpy.types.Operator):
    bl_idname = "luxcore.select_crf"
    bl_label = "Select Preset"
    bl_description = "Camera Response Function presets"
    bl_property = "crf_preset"

    callback_string = []

    def cb_crf_preset(self, context):
        items = [(name, name.replace("_", " "), "", i) for i, name in enumerate(crf_preset_names)]
        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        LUXCORE_OT_select_crf.callback_strings = items
        return items

    crf_preset: EnumProperty(name="CRF Preset",
                              description="Camera Response Function presets",
                              items=cb_crf_preset)

    @classmethod
    def poll(cls, context):
        return context.scene and context.scene.camera

    def execute(self, context):
        camera = context.scene.camera
        imagepipeline = camera.data.luxcore.imagepipeline
        imagepipeline.camera_response_func.preset = self.crf_preset
        # This is a trick to force a camera update during viewport render
        # (Blender does not notify us if we only change a custom property)
        camera.data.lens = camera.data.lens
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


class LUXCORE_OT_set_raw_view_transform(bpy.types.Operator):
    bl_idname = "luxcore.set_raw_view_transform"
    bl_label = "Set View Transform to Raw"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        return context.scene

    def execute(self, context):
        context.scene.view_settings.view_transform = "Raw"
        context.scene.view_settings.gamma = 1
        return {'FINISHED'}

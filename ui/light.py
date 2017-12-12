import bl_ui
import bpy


NARROW_UI_WIDTH = 280


class LuxCoreLampHeader(bl_ui.properties_data_lamp.DataButtonsPanel, bpy.types.Panel):
    """
    Lamp UI Panel
    """
    COMPAT_ENGINES = "LUXCORE"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.lamp and engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        lamp = context.lamp

        if context.lamp is not None:
            wide_ui = context.region.width > NARROW_UI_WIDTH

            if wide_ui:
                layout.prop(lamp.luxcore, "type", expand=True)
            else:
                layout.prop(lamp.luxcore, "type", text="")

            layout.prop(lamp.luxcore, "gain")
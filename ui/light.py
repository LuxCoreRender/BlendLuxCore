import bl_ui
import bpy


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

    def draw_image_controls(self, context):
        layout = self.layout
        lamp = context.lamp
        layout.prop(lamp.luxcore, "image")
        if lamp.luxcore.image:
            layout.prop(lamp.luxcore, "gamma")
        # TODO: load image button

    def draw(self, context):
        layout = self.layout
        lamp = context.lamp

        layout.prop(lamp, "type", expand=True)

        layout.prop(lamp.luxcore, "rgb_gain")
        layout.prop(lamp.luxcore, "gain")
        layout.prop(lamp.luxcore, "samples")
        # TODO: id

        if lamp.type == "POINT":
            layout.prop(lamp.luxcore, "power")
            layout.prop(lamp.luxcore, "efficency")
            layout.prop(lamp.luxcore, "iesfile")

            if lamp.luxcore.iesfile:
                layout.prop(lamp.luxcore, "flipz")

            self.draw_image_controls(context)

        elif lamp.type == "SUN":
            layout.prop(lamp.luxcore, "sun_type", expand=True)

            if lamp.luxcore.sun_type == "sun":
                layout.prop(lamp.luxcore, "relsize")
                layout.prop(lamp.luxcore, "turbidity")
            elif lamp.luxcore.sun_type == "distant":
                layout.prop(lamp.luxcore, "theta")

        elif lamp.type == "SPOT":
            layout.prop(lamp.luxcore, "spot_type", expand=True)
            layout.prop(lamp, "spot_size")

            if lamp.luxcore.spot_type == "spot":
                layout.prop(lamp, "spot_blend")
                layout.prop(lamp.luxcore, "power")
                self.draw_image_controls(context)

            layout.prop(lamp, "show_cone")

        elif lamp.type == "HEMI":
            self.draw_image_controls(context)
            layout.prop(lamp.luxcore, "blacklowerhemisphere")

        elif lamp.type == "AREA":
            layout.prop(lamp, "shape", expand=True)
            row = layout.row()
            row.prop(lamp, "size", text="Size X")
            row.prop(lamp, "size_y")


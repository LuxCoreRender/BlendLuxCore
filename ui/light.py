import bl_ui
import bpy

# TODO: add warning/info label about gain problems (e.g. "why is my HDRI black when a sun is in the scene")


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
        layout.template_ID(lamp.luxcore, "image", open="image.open")
        if lamp.luxcore.image:
            layout.prop(lamp.luxcore, "gamma")

    def draw(self, context):
        layout = self.layout
        lamp = context.lamp

        layout.prop(lamp, "type", expand=True)

        split = layout.split(percentage=0.33)
        split.prop(lamp.luxcore, "rgb_gain", text="")
        split.prop(lamp.luxcore, "gain")
        # TODO: id

        layout.separator()

        # TODO: split this stuff into separate panels for each light type?
        if lamp.type == "POINT":
            row = layout.row(align=True)
            row.prop(lamp.luxcore, "power")
            row.prop(lamp.luxcore, "efficacy")

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
            row = layout.row(align=True)
            row.prop(lamp.luxcore, "power")
            row.prop(lamp.luxcore, "efficacy")

            row = layout.row(align=True)
            row.prop(lamp, "spot_size")
            if lamp.luxcore.image is None:
                # projection does not have this property
                row.prop(lamp, "spot_blend")

            self.draw_image_controls(context)

            layout.prop(lamp, "show_cone")

        elif lamp.type == "HEMI":
            self.draw_image_controls(context)
            layout.prop(lamp.luxcore, "sampleupperhemisphereonly")

        elif lamp.type == "AREA":
            row = layout.row(align=True)
            row.prop(lamp.luxcore, "power")
            row.prop(lamp.luxcore, "efficacy")

            if lamp.luxcore.is_laser:
                layout.prop(lamp, "size", text="Size")
            else:
                col = layout.column(align=True)
                # the shape controls should be two horizontal buttons
                sub = col.row(align=True)
                sub.prop(lamp, "shape", expand=True)
                # put the size controls horizontal, too
                row = col.row(align=True)

                if lamp.shape == "SQUARE":
                    row.prop(lamp, "size", text="Size")
                else:
                    row.prop(lamp, "size", text="Size X")
                    row.prop(lamp, "size_y")

            layout.prop(lamp.luxcore, "is_laser")


class LuxCoreLampPerformance(bl_ui.properties_data_lamp.DataButtonsPanel, bpy.types.Panel):
    """
    Lamp UI Panel, shows stuff that affects the performance of the render
    """
    COMPAT_ENGINES = "LUXCORE"
    bl_label = "Performance"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.lamp and engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        lamp = context.lamp

        layout.prop(lamp.luxcore, "samples")
        layout.prop(lamp.luxcore, "importance")

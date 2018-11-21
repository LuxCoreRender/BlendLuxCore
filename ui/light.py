from bl_ui.properties_data_lamp import DataButtonsPanel
from bpy.types import Panel
from . import icons

# TODO: add warning/info label about gain problems (e.g. "why is my HDRI black when a sun is in the scene")


class LUXCORE_LAMP_PT_context_lamp(DataButtonsPanel, Panel):
    """
    Lamp UI Panel
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.lamp and engine == "LUXCORE"

    def draw_image_controls(self, context):
        layout = self.layout
        lamp = context.lamp

        col = layout.column(align=True)
        col.label("Image:")
        col.template_ID(lamp.luxcore, "image", open="image.open")
        if lamp.luxcore.image:
            col.prop(lamp.luxcore, "gamma")
        lamp.luxcore.image_user.draw(layout, context.scene)

    def draw_ies_controls(self, context):
        layout = self.layout
        lamp = context.lamp

        col = layout.column(align=True)
        col.prop(lamp.luxcore.ies, "use", toggle=True)

        if lamp.luxcore.ies.use:
            box = col.box()

            row = box.row()
            row.label("IES Data:")
            row.prop(lamp.luxcore.ies, "file_type", expand=True)

            if lamp.luxcore.ies.file_type == "TEXT":
                box.prop(lamp.luxcore.ies, "file_text")
                iesfile = lamp.luxcore.ies.file_text
            else:
                # lamp.luxcore.ies.file_type == "PATH":
                box.prop(lamp.luxcore.ies, "file_path")
                iesfile = lamp.luxcore.ies.file_path

            sub = box.row(align=True)
            sub.active = bool(iesfile)
            sub.prop(lamp.luxcore.ies, "flipz")
            sub.prop(lamp.luxcore.ies, "map_width")
            sub.prop(lamp.luxcore.ies, "map_height")

    def draw(self, context):
        layout = self.layout
        lamp = context.lamp

        layout.prop(lamp, "type", expand=True)

        split = layout.split()

        col = split.column(align=True)
        col.prop(lamp.luxcore, "rgb_gain", text="")
        col.prop(lamp.luxcore, "gain")

        col = split.column(align=True)
        op = col.operator("luxcore.switch_space_data_context", text="Show Light Groups")
        op.target = "SCENE"
        lightgroups = context.scene.luxcore.lightgroups
        col.prop_search(lamp.luxcore, "lightgroup",
                        lightgroups, "custom",
                        icon=icons.LIGHTGROUP, text="")

        layout.separator()

        # TODO: split this stuff into separate panels for each light type?
        if lamp.type == "POINT":
            row = layout.row(align=True)
            row.prop(lamp.luxcore, "power")
            row.prop(lamp.luxcore, "efficacy")

            layout.prop(lamp.luxcore, "radius")

            # IES Data
            self.draw_ies_controls(context)

            self.draw_image_controls(context)

        elif lamp.type == "SUN":
            layout.prop(lamp.luxcore, "sun_type", expand=True)

            if lamp.luxcore.sun_type == "sun":
                world = context.scene.world
                if world and world.luxcore.light == "sky2" and world.luxcore.sun != context.object:
                    layout.operator("luxcore.attach_sun_to_sky", icon=icons.WORLD)
                layout.prop(lamp.luxcore, "relsize")
                layout.prop(lamp.luxcore, "turbidity")
            elif lamp.luxcore.sun_type == "distant":
                layout.prop(lamp.luxcore, "theta")

        elif lamp.type == "SPOT":
            row = layout.row(align=True)
            row.prop(lamp.luxcore, "power")
            row.prop(lamp.luxcore, "efficacy")

            row = layout.row(align=True)
            row.prop(lamp, "spot_size", slider=True)
            if lamp.luxcore.image is None:
                # projection does not have this property
                row.prop(lamp, "spot_blend", slider=True)
            layout.prop(lamp, "show_cone")

            self.draw_image_controls(context)

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
                row = layout.row()
                if context.object:
                    row.prop(context.object.luxcore, "visible_to_camera")
                row.prop(lamp.luxcore, "spread_angle", slider=True)

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

                self.draw_ies_controls(context)

            layout.prop(lamp.luxcore, "is_laser")


class LUXCORE_LAMP_PT_performance(DataButtonsPanel, Panel):
    """
    Lamp UI Panel, shows stuff that affects the performance of the render
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Performance"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.lamp and engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        lamp = context.lamp

        layout.prop(lamp.luxcore, "importance")

        if lamp.type == "HEMI":
            # infinite (with image) and constantinfinte lights
            layout.prop(lamp.luxcore, "visibilitymap_enable")


class LUXCORE_LAMP_PT_visibility(DataButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Visibility"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine

        visible = False
        if context.lamp:
            # Visible for sky2, sun, infinite, constantinfinite
            if context.lamp.type == "SUN" and context.lamp.luxcore.sun_type == "sun":
                visible = True
            elif context.lamp.type == "HEMI":
                visible = True

        return context.lamp and engine == "LUXCORE" and visible

    def draw(self, context):
        layout = self.layout
        lamp = context.lamp

        # These settings only work with PATH and TILEPATH, not with BIDIR
        enabled = context.scene.luxcore.config.engine == "PATH"

        sub = layout.column()
        sub.enabled = enabled
        sub.label("Visibility for indirect light rays:")
        row = sub.row()
        row.prop(lamp.luxcore, "visibility_indirect_diffuse")
        row.prop(lamp.luxcore, "visibility_indirect_glossy")
        row.prop(lamp.luxcore, "visibility_indirect_specular")

        if not enabled:
            layout.label("Only supported by Path engines (not by Bidir)", icon=icons.INFO)

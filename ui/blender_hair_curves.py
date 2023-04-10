from bl_ui.properties_data_curves import DataButtonsPanel
from bpy.types import Panel
from ..ui import icons
from ..ui.icons import icon_manager

class LUXCORE_DATA_PT_curve_hair(DataButtonsPanel, Panel):
    bl_label = "LuxCore Hair Settings"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_order = 10

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout

        obj = context.object
        settings = obj.luxcore.hair

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(settings, "hair_size")

        col = layout.column(align=True)
        col.prop(settings, "root_width")
        col.prop(settings, "tip_width")
        col.prop(settings, "width_offset")

        layout.prop(settings, "tesseltype")

        if "adaptive" in settings.tesseltype:
            col = layout.column(align=True)
            col.prop(settings, "adaptive_maxdepth")
            col.prop(settings, "adaptive_error")

        if settings.tesseltype.startswith("solid"):
            layout.prop(settings, "solid_sidecount")

            col = layout.column(align=True)
            col.prop(settings, "solid_capbottom")
            col.prop(settings, "solid_captop")

        layout.prop(settings, "copy_uv_coords")

        # UV map selection
        box = layout.box()
        box.enabled = settings.copy_uv_coords or settings.export_color == "uv_texture_map"
        col = box.column()
        col.prop(settings, "use_active_uv_map")

        if settings.use_active_uv_map:
            if obj.parent.data.uv_layers:
                active_uv = obj.parent.data.uv_layers[obj.data.surface_uv_map]
                if active_uv:
                    row = col.row(align=True)
                    row.label(text="UV Map")
                    row.label(text=active_uv.name, icon="GROUP_UVS")
        else:
            col.prop_search(settings, "uv_map_name",
                            obj.parent.data, "uv_layers",
                            icon="GROUP_UVS")

        if not obj.parent.data.uv_layers:
            row = col.row()
            row.label(text="No UV map", icon=icons.WARNING)
            row.operator("mesh.uv_texture_add", icon=icons.ADD)

        # Vertex color settings
        box = layout.box()
        box.prop(settings, "export_color")

        if settings.export_color == "vertex_color":
            col = box.column(align=True)
            col.prop(settings, "use_active_vertex_color_layer")
        #
        #     if settings.use_active_vertex_color_layer:
        #         if obj.data.vertex_colors:
        #             active_vcol_layer = utils.find_active_vertex_color_layer(obj.data.vertex_colors)
        #             if active_vcol_layer:
        #                 row = col.row(align=True)
        #                 row.label(text="Vertex Colors")
        #                 row.label(text=active_vcol_layer.name, icon="GROUP_VCOL")
        #     else:
        #         col.prop_search(settings, "vertex_color_layer_name",
        #                         obj.data, "vertex_colors",
        #                         icon="GROUP_VCOL", text="Vertex Colors")
        #
        #     if not obj.data.vertex_colors:
        #         row = col.row()
        #         row.label(text="No Vertex Colors", icon=icons.WARNING)
        #         row.operator("mesh.vertex_color_add", icon=icons.ADD)
        #
        elif settings.export_color == "uv_texture_map":
            box.template_ID(settings, "image", open="image.open")
            if settings.image:
                box.prop(settings, "gamma")
            settings.image_user.draw(box, context.scene)

        col = box.column(align=True)
        col.prop(settings, "root_color")
        col.prop(settings, "tip_color")

        layout.prop(settings, "instancing")



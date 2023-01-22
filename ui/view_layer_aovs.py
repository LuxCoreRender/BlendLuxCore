from bl_ui.properties_view_layer import ViewLayerButtonsPanel
from bpy.types import Panel
from . import icons
from .icons import icon_manager

class LUXCORE_RENDERLAYER_PT_aovs(ViewLayerButtonsPanel, Panel):
    bl_label = "LuxCore AOVs"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_order = 2

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout

        engine_is_path = context.scene.luxcore.config.engine == "PATH"

        if not engine_is_path:
            layout.label(text="The Bidir engine does not support all AOVs", icon=icons.INFO)



class LUXCORE_RENDERLAYER_PT_aovs_basic(ViewLayerButtonsPanel, Panel):
    bl_label = "Basic Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs

        # Supported by BIDIR
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
        col = flow.column()
        col.prop(aovs, "rgb")
        col.prop(aovs, "rgba")
        col.prop(aovs, "alpha")
        col = flow.column()
        col.prop(aovs, "depth")
        col.prop(aovs, "albedo")


class LUXCORE_RENDERLAYER_PT_aovs_material_object(ViewLayerButtonsPanel, Panel):
    bl_label = "Material/Object Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs

        # Supported by BIDIR
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
        col = flow.column()
        col.prop(aovs, "material_id")
        col.prop(aovs, "material_id_color")

        col = flow.column()
        col.prop(aovs, "object_id")


class LUXCORE_RENDERLAYER_PT_aovs_light(ViewLayerButtonsPanel, Panel):
    bl_label = "Light Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs
        config = context.scene.luxcore.config
        engine_is_path = config.engine == "PATH"

        # Not supported by BIDIR
        layout.active = engine_is_path

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
        col = flow.column()
        col.prop(aovs, "emission")
        col = flow.column()
        col.prop(aovs, "caustic")

        if aovs.caustic:
            if config.engine == "BIDIR":
                layout.label(text="Caustic AOV will contain unexpected results with Bidir", icon=icons.WARNING)
            elif config.engine == "PATH" and not config.path.hybridbackforward_enable:
                layout.label(text="Enable light tracing for caustic AOV", icon=icons.WARNING)

        col = layout.column()
        col.use_property_split = False
        col.use_property_decorate = False

        col.label(text="Direct Light")

        row = col.row(align=True)
        row.label(text="Diffuse")
        row.prop(aovs, "direct_diffuse", toggle=True)
        row.prop(aovs, "direct_diffuse_reflect", toggle=True)
        row.prop(aovs, "direct_diffuse_transmit", toggle=True)

        row = col.row(align=True)
        row.label(text="Glossy")
        row.prop(aovs, "direct_glossy", toggle=True)
        row.prop(aovs, "direct_glossy_reflect", toggle=True)
        row.prop(aovs, "direct_glossy_transmit", toggle=True)

        col.label(text="Indirect Light")

        row = col.row(align=True)
        row.label(text="Diffuse")
        row.prop(aovs, "indirect_diffuse", toggle=True)
        row.prop(aovs, "indirect_diffuse_reflect", toggle=True)
        row.prop(aovs, "indirect_diffuse_transmit", toggle=True)

        row = col.row(align=True)
        row.label(text="Glossy")
        row.prop(aovs, "indirect_glossy", toggle=True)
        row.prop(aovs, "indirect_glossy_reflect", toggle=True)
        row.prop(aovs, "indirect_glossy_transmit", toggle=True)

        row = col.row(align=True)
        row.label(text="Specular")
        row.prop(aovs, "indirect_specular", toggle=True)
        row.prop(aovs, "indirect_specular_reflect", toggle=True)
        row.prop(aovs, "indirect_specular_transmit", toggle=True)


class LUXCORE_RENDERLAYER_PT_aovs_shadow(ViewLayerButtonsPanel, Panel):
    bl_label = "Shadow Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"
    
    def draw(self, context):
        layout = self.layout

        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs
        engine_is_path = context.scene.luxcore.config.engine == "PATH"

        # Not supported by BIDIR
        layout.active = engine_is_path

        row = layout.row(align=True)
        row.label(text="Shadow Mask")
        row.prop(aovs, "direct_shadow_mask", toggle=True)
        row.prop(aovs, "indirect_shadow_mask", toggle=True)


class LUXCORE_RENDERLAYER_PT_aovs_geometry(ViewLayerButtonsPanel, Panel):
    bl_label = "Geometry Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs
        
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        # Supported by BIDIR
        col = flow.column()
        col.prop(aovs, "position")
        col.prop(aovs, "shading_normal")
        col.prop(aovs, "avg_shading_normal")
        col = flow.column()
        col.prop(aovs, "geometry_normal")
        col.prop(aovs, "uv")


class LUXCORE_RENDERLAYER_PT_aovs_render(ViewLayerButtonsPanel, Panel):
    bl_label = "Render Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs
        engine_is_path = context.scene.luxcore.config.engine == "PATH"

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        # Not supported by BIDIR
        col = flow.column()
        col.active = engine_is_path
        col.prop(aovs, "irradiance")
        col.prop(aovs, "raycount")
        col.prop(aovs, "convergence")

        # Supported by BIDIR
        col = flow.column()
        col.prop(aovs, "noise")
        col.prop(aovs, "samplecount")

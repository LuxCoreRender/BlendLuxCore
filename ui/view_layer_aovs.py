from bl_ui.properties_view_layer import ViewLayerButtonsPanel
from bpy.types import Panel
from ..ui import icons


class LUXCORE_RENDERLAYER_PT_aovs(ViewLayerButtonsPanel, Panel):
    bl_label = "LuxCore Arbitrary Output Variables (AOVs)"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs
        engine_is_path = context.scene.luxcore.config.engine == "PATH"

        if not engine_is_path:
            layout.label(text="The Bidir engine only supports a few AOVs", icon=icons.INFO)



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
        engine_is_path = context.scene.luxcore.config.engine == "PATH"
        
        
        # Supported by BIDIR
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
        col = flow.column()
        col.prop(aovs, "rgb")
        col = flow.column()
        col.prop(aovs, "rgba")
        col = flow.column()
        col.prop(aovs, "alpha")
        col = flow.column()
        col.prop(aovs, "depth")
        col = flow.column()
        col.prop(aovs, "albedo")


class LUXCORE_RENDERLAYER_PT_aovs_material_object(ViewLayerButtonsPanel, Panel):
    bl_label = "Material/Object Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"
    lux_predecessor = "LUXCORE_RENDERLAYER_PT_aovs_basic"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs
        engine_is_path = context.scene.luxcore.config.engine == "PATH"
              
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
        # Supported by BIDIR
        col = flow.column()
        col.prop(aovs, "material_id")
        col = flow.column()
        col.prop(aovs, "material_id_color")
        col = flow.column()
        col.prop(aovs, "object_id")
        
        # Not supported by BIDIR
        col = flow.column()
        col.enabled = engine_is_path
        col.prop(aovs, "emission")


class LUXCORE_RENDERLAYER_PT_aovs_direct_light(ViewLayerButtonsPanel, Panel):
    bl_label = "Direct Light Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"
    lux_predecessor = "LUXCORE_RENDERLAYER_PT_aovs_material_object"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs
        engine_is_path = context.scene.luxcore.config.engine == "PATH"

        # Not supported by BIDIR
        layout.enabled = engine_is_path
                
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
        col = flow.column()
        col.prop(aovs, "direct_diffuse")
        col = flow.column()
        col.prop(aovs, "direct_glossy")


class LUXCORE_RENDERLAYER_PT_aovs_indirect_light(ViewLayerButtonsPanel, Panel):
    bl_label = "Indirect Light Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"
    lux_predecessor = "LUXCORE_RENDERLAYER_PT_aovs_direct_light"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs
        engine_is_path = context.scene.luxcore.config.engine == "PATH"
        
        # Not supported by BIDIR
        layout.enabled = engine_is_path
        
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
        col = flow.column()
        col.prop(aovs, "indirect_diffuse")
        col = flow.column()
        col.prop(aovs, "indirect_glossy")
        col = flow.column()
        col.prop(aovs, "indirect_specular")


class LUXCORE_RENDERLAYER_PT_aovs_geometry(ViewLayerButtonsPanel, Panel):
    bl_label = "Geometry Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"
    lux_predecessor = "LUXCORE_RENDERLAYER_PT_aovs_indirect_light"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs
        engine_is_path = context.scene.luxcore.config.engine == "PATH"
        
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        # Supported by BIDIR
        col = flow.column()
        col.prop(aovs, "position")
        col = flow.column()
        col.prop(aovs, "shading_normal")
        col = flow.column()
        col.prop(aovs, "avg_shading_normal")
        col = flow.column()
        col.prop(aovs, "geometry_normal")
        col = flow.column()
        col.prop(aovs, "uv")


class LUXCORE_RENDERLAYER_PT_aovs_shadow(ViewLayerButtonsPanel, Panel):
    bl_label = "Shadow Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"
    lux_predecessor = "LUXCORE_RENDERLAYER_PT_aovs_geometry"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        active_layer = context.window.view_layer
        aovs = active_layer.luxcore.aovs
        engine_is_path = context.scene.luxcore.config.engine == "PATH"
        
        # Not supported by BIDIR
        layout.enabled = engine_is_path
        
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
        col = flow.column()
        col.prop(aovs, "direct_shadow_mask")
        col = flow.column()
        col.prop(aovs, "indirect_shadow_mask")


class LUXCORE_RENDERLAYER_PT_aovs_render(ViewLayerButtonsPanel, Panel):
    bl_label = "Render Information"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDERLAYER_PT_aovs"
    lux_predecessor = "LUXCORE_RENDERLAYER_PT_aovs_shadow"

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
        col.enabled = engine_is_path
        col.prop(aovs, "irradiance")
        col = flow.column()
        col.enabled = engine_is_path
        col.prop(aovs, "raycount")

        # Supported by BIDIR
        col = flow.column()
        col.prop(aovs, "convergence")
        col = flow.column()
        col.prop(aovs, "noise")
        col = flow.column()
        col.prop(aovs, "samplecount")

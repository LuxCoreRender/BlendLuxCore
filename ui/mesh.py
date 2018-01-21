from bl_ui.properties_data_mesh import MeshButtonsPanel
from bpy.types import Panel


class LUXCORE_DATA_PT_normals(MeshButtonsPanel, Panel):
    bl_label = "Normals"
    COMPAT_ENGINES = {"LUXCORE"}

    def draw(self, context):
        layout = self.layout

        mesh = context.mesh

        split = layout.split()

        col = split.column()
        col.enabled = False  # LuxCore does not support auto smoothing
        col.prop(mesh, "use_auto_smooth")
        sub = col.column()
        sub.active = mesh.use_auto_smooth and not mesh.has_custom_normals
        sub.prop(mesh, "auto_smooth_angle", text="Angle")

        col = layout.column(align=True)
        icon = "ERROR" if mesh.use_auto_smooth else "INFO"
        col.label("LuxCore does not support Auto Smooth, use Edge Split instead:", icon=icon)
        op = col.operator("object.modifier_add", text="Add Edge Split Modifier", icon="MOD_EDGESPLIT")
        op.type = "EDGE_SPLIT"

        split.prop(mesh, "show_double_sided")
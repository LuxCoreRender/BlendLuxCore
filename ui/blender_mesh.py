from bl_ui.properties_data_mesh import MeshButtonsPanel
from bpy.types import Panel
from .. import utils


class LUXCORE_DATA_PT_proxy(MeshButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    #bl_context = "object"
    bl_label = "LuxCore Proxy Settings"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        mesh = context.object.data
        
        layout.prop(mesh.luxcore, "use_proxy")
        row = layout.row()
        col = row.column(align=True)

        if not mesh.luxcore.use_proxy:
            col.operator("luxcore.proxy_new", icon="EXPORT")
        else:
            box = row.box()
            box.label("PLY Meshes:")
            col = row.column(align=True)

            col.operator("luxcore.proxy_add", icon="ZOOMIN", text="")
            col.operator("luxcore.proxy_remove", icon="ZOOMOUT", text="")
            
            for proxy in mesh.luxcore.proxies:                
                box.prop(proxy, "filepath", text=proxy.name)

            box.prop(mesh.luxcore, "proxies")

from bl_ui.properties_object import ObjectButtonsPanel
from bpy.types import Panel
from .. import utils


class LUXCORE_OBJECT_PT_object(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_context = "object"
    bl_label = "LuxCore Object Settings"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        layout.prop(obj.luxcore, "visible_to_camera")

        # Motion blur settings
        cam = context.scene.camera
        if cam:
            motion_blur = cam.data.luxcore.motion_blur
            object_blur = motion_blur.enable and motion_blur.object_blur

            if not motion_blur.enable:
                layout.label("Motion blur disabled in camera settings", icon="INFO")
            elif not motion_blur.object_blur:
                layout.label("Object blur disabled in camera settings", icon="INFO")
        else:
            layout.label("No camera in scene", icon="INFO")
            object_blur = False

        row = layout.row()
        row.active = object_blur
        row.prop(obj.luxcore, "enable_motion_blur")
        # Instancing can cost performance, so inform the user when it happens
        if utils.use_obj_motion_blur(obj, context.scene):
            layout.label("Object will be exported as instance", icon="INFO")


class LUXCORE_OBJECT_PT_proxy(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_context = "object"
    bl_label = "LuxCore Proxy Settings"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        
        layout.prop(obj.luxcore, "use_proxy")
        row = layout.row()
        col = row.column(align=True)

        if not obj.luxcore.use_proxy:
            col.operator("luxcore.proxy_new", text="Create Proxy")
        else:
            box = layout.box()
            box.label("Proxies:")            
            for proxy in obj.luxcore.proxies:                
                box.prop(proxy, "filepath", text=proxy.name)
            
            box.prop(obj.luxcore, "proxies")


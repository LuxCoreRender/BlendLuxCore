import bpy
from time import time, sleep
from .bin import pyluxcore
from .draw import FrameBuffer, FrameBufferFinal
from . import export

# Have to import everything with classes which need to be registered
from . import nodes, operators, properties, ui
from .nodes import materials

bl_info = {
    "name": "LuxCore",
    "author": "Simon Wendsche (B.Y.O.B.)",
    "version": (2, 0),
    "blender": (2, 77, 0),
    "category": "Render",
    "location": "Info header, render engine menu",
    "description": "LuxCore integration for Blender",
    "warning": "Alpha Version, incomplete",
    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}


########################
# def init():
#     bpy.types.Object.luxcore = bpy.props.PointerProperty(type=LuxCoreMaterialProps)
#     bpy.types.Mesh.test = bpy.props.PointerProperty(type=TestPropGroup)
#
# class LuxCoreMaterialProps(bpy.types.PropertyGroup):
#     node_tree = bpy.props.PointerProperty(name="Node Tree", type=bpy.types.NodeTree)
#     test = bpy.props.PointerProperty(name="test", type=bpy.types.Object)
#     test_str = bpy.props.StringProperty(name="teststr")
#
# class TestPropGroup(bpy.types.PropertyGroup):
#     test = bpy.props.PointerProperty(name="test", type=bpy.types.Object)
########################

def register():
    ui.register()
    nodes.materials.register()
    bpy.utils.register_module(__name__, verbose=True)

    properties.init()

    # bpy.types.Material.luxcore = bpy.props.PointerProperty(type=properties.material.LuxCoreMaterialProps)
    # bpy.types.Material.test = bpy.props.PointerProperty(type=bpy.types.Object)
    #
    # bpy.types.Object.testgroup = bpy.props.PointerProperty(type=TestPropGroup)


def unregister():
    ui.unregister()
    nodes.materials.unregister()
    bpy.utils.unregister_module(__name__)


# TODO move to engine module
class LuxCoreRenderEngine(bpy.types.RenderEngine):
    bl_idname = "LUXCORE"
    bl_label = "LuxCore"
    bl_use_preview = False  # TODO: disabled for now
    bl_use_shading_nodes_custom = True

    def __init__(self):
        print("init")
        self._framebuffer = None
        self._session = None
        self._exporter = export.Exporter()

    def __del__(self):
        # Note: this method is also called when unregister() is called (for some reason I don't understand)
        print("LuxCoreRenderEngine del")
        if hasattr(self, "_session") and self._session:
            print("del: stopping session")
            self._session.Stop()
            del self._session

    def update(self, data, scene):
        """Export scene data for render"""
        assert self._session is None
        self.update_stats("Export", "exporting...")

        self._session = self._exporter.create_session(scene)

    def render(self, scene):
        assert self._session is not None
        self.update_stats("Render", "rendering...")
        self._framebuffer = FrameBufferFinal(scene)
        self._session.Start()
        self._framebuffer.draw(self, self._session)

        start = time()
        interval = 3
        while not self.test_break():
            sleep(1 / 50)
            if time() - start > interval:
                self._framebuffer.draw(self, self._session)

        self._framebuffer.draw(self, self._session)

    def view_update(self, context):
        self.view_update_lux(context)

    def view_update_lux(self, context, changes=None):
        print("view_update")

        if self._session is None:
            self._session = self._exporter.create_session(context.scene, context)
            self._session.Start()
            return

        if changes is None:
            changes = self._exporter.get_changes(context)
        self._exporter.update(context, self._session, changes)

    def view_draw(self, context):
        # TODO: film resize update

        changes = self._exporter.get_changes(context)

        if changes & export.Change.REQUIRES_VIEW_UPDATE:
            if changes & export.Change.CONFIG:
                # Film resize requires a new framebuffer
                self._framebuffer = FrameBuffer(context)
            self.view_update_lux(context, changes)
            return
        elif changes & export.Change.CAMERA:
            # Only update allowed in view_draw is a camera update, for everything else we call view_update_lux()
            self._exporter.update(context, self._session, export.Change.CAMERA)

        if self._framebuffer is None:
            self._framebuffer = FrameBuffer(context)

        if self._session:
            self._session.UpdateStats()
            self._session.WaitNewFrame()
            self._framebuffer.update(self._session)

        region_size = context.region.width, context.region.height
        view_camera_offset = list(context.region_data.view_camera_offset)
        self._framebuffer.draw(region_size, view_camera_offset)
        self.tag_redraw()

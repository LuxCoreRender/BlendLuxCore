from time import time
from .. import export
from ..draw.viewport import FrameBuffer
from ..utils import render as utils_render


def export_obj(obj, depsgraph, luxcore_scene):
    # Avoid annoying None checks later on.
    if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
        return None

    object_eval = obj.evaluated_get(depsgraph)
    mesh = object_eval.to_mesh()

    ##########################

    mesh.calc_loop_triangles()
    loopTriPtr = mesh.loop_triangles[0].as_pointer()
    loopTriCount = len(mesh.loop_triangles)
    loopPtr = mesh.loops[0].as_pointer()
    loopCount = len(mesh.loops)
    vertPtr = mesh.vertices[0].as_pointer()
    vertCount = len(mesh.vertices)
    polyCount = len(mesh.polygons)
    polyPtr = mesh.polygons[0].as_pointer()

    name = "testmesh"
    matIndex = 0
    # mesh_transform = utils.matrix_to_list(obj.matrix_world)
    res = luxcore_scene.DefineBlenderMeshNew(name,
                                             loopTriCount, loopTriPtr,
                                             loopCount, loopPtr,
                                             vertCount, vertPtr,
                                             polyCount, polyPtr,
                                             matIndex)

    ##########################
    # Remove temporary mesh.
    object_eval.to_mesh_clear()

    ##########################




def view_update(engine, context, depsgraph, changes=None):
    scene = depsgraph.scene

    if engine.session is None:
        # engine.exporter = export.Exporter(scene)
        # # Note: in viewport render, the user can't cancel the
        # # export (Blender limitation), so we don't pass engine here
        # engine.session = engine.exporter.create_session(context)
        # engine.session.Start()

        # Just for mesh export testing
        from ..bin import pyluxcore
        luxcore_scene = pyluxcore.Scene()
        scene_props = pyluxcore.Properties()
        scene_props.SetFromString("""
            scene.camera.lookat.orig = 5 -8 5
            scene.camera.lookat.target = 0.0 0.0 0.4
            
            scene.materials.testmat.type = "matte"
            scene.materials.testmat.kd = 0 0.5 0.5
            
            scene.objects.testobj.shape = "testmesh"
            scene.objects.testobj.material = "testmat"
            
            scene.lights.testlight.type = "constantinfinite"
            #scene.lights.testlight.position = -2 0.3 1.6
            """)
        export_obj(depsgraph.objects["Cube"], depsgraph, luxcore_scene)
        luxcore_scene.Parse(scene_props)
        config_props = pyluxcore.Properties()
        from .. import utils
        filmsize = utils.calc_filmsize(scene, context)
        config_props.Set(pyluxcore.Property("film.width", filmsize[0]))
        config_props.Set(pyluxcore.Property("film.height", filmsize[1]))
        renderconfig = pyluxcore.RenderConfig(config_props, luxcore_scene)
        engine.session = pyluxcore.RenderSession(renderconfig)
        print("session created")
        engine.session.Start()

        # import time
        # time.sleep(3)
        # engine.session.GetFilm().SaveOutput(r"C:\Users\Simon\Desktop\test.png", pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE, pyluxcore.Properties())


    pass
    # if engine.framebuffer:
    #     engine.framebuffer.reset_denoiser()
    #
    # scene = context.scene
    # scene.luxcore.errorlog.clear()
    #
    # if engine.session is None:
    #     print("=" * 50)
    #     print("[Engine/Viewport] New session")
    #     try:
    #         engine.update_stats("Creating Render Session...", "")
    #         engine.exporter = export.Exporter(scene)
    #         # Note: in viewport render, the user can't cancel the
    #         # export (Blender limitation), so we don't pass engine here
    #         engine.session = engine.exporter.create_session(context)
    #         engine.session.Start()
    #         engine.viewport_start_time = time()
    #         return
    #     except Exception as error:
    #         del engine.session
    #         engine.session = None
    #         # Reset the exporter to invalidate all caches
    #         engine.exporter = export.Exporter(scene)
    #
    #         engine.update_stats("Error: ", str(error))
    #         scene.luxcore.errorlog.add_error(error)
    #
    #         import traceback
    #         traceback.print_exc()
    #         return
    #
    # if changes is None:
    #     changes = engine.exporter.get_changes(context)
    #
    # if changes & export.Change.CONFIG:
    #     # Film resize requires a new framebuffer
    #     engine.framebuffer = FrameBuffer(context)
    #
    # # We have to re-assign the session because it might have been replaced due to filmsize change
    # engine.session = engine.exporter.update(context, engine.session, changes)
    #
    # if changes:
    #     engine.viewport_start_time = time()
    

def view_draw(engine, context, depsgraph):
    scene = depsgraph.scene

    if not engine.framebuffer or engine.framebuffer.needs_replacement(context, scene):
        print("new framebuffer")
        engine.framebuffer = FrameBuffer(engine, context, scene)

    if engine.session:
        try:
            engine.session.UpdateStats()
        except RuntimeError as error:
            print("[Engine/Viewport] Error during UpdateStats():", error)
        engine.session.WaitNewFrame()
        engine.framebuffer.update(engine.session, scene)
        engine.framebuffer.draw(engine, context, scene)
    engine.tag_redraw()

    # scene = context.scene
    #
    # # Check for changes because some actions in Blender (e.g. moving the viewport
    # # camera) do not trigger a view_update() call, but only a view_draw() call.
    # changes = engine.exporter.get_changes(context)
    #
    # if changes & export.Change.REQUIRES_VIEW_UPDATE:
    #     engine.tag_redraw()
    #     view_update(engine, context, changes)
    #     return
    # elif changes & export.Change.CAMERA:
    #     # Only update in view_draw if it is a camera update,
    #     # for everything else we call view_update().
    #     # We have to re-assign the session because it might have been
    #     # replaced due to filmsize change.
    #     engine.session = engine.exporter.update(context, engine.session, export.Change.CAMERA)
    #     engine.viewport_start_time = time()
    #
    # # On startup we don't have a framebuffer yet
    # if engine.framebuffer is None:
    #     engine.framebuffer = FrameBuffer(context)
    # framebuffer = engine.framebuffer
    #
    # # Check if we need to pause the viewport render
    # # (note: the LuxCore stat "stats.renderengine.time" is not reliable here)
    # rendered_time = time() - engine.viewport_start_time
    # halt_time = scene.luxcore.viewport.halt_time
    # status_message = ""
    #
    # if rendered_time > halt_time:
    #     if not engine.session.IsInPause():
    #         print("[Engine/Viewport] Pausing session")
    #         engine.session.Pause()
    #     status_message = "(Paused)"
    #
    #     if framebuffer.denoiser_result_cached:
    #         status_message = "(Paused, Denoiser Done)"
    #     else:
    #         if framebuffer.is_denoiser_active():
    #             if framebuffer.is_denoiser_done():
    #                 status_message = "(Paused, Denoiser Done)"
    #                 framebuffer.load_denoiser_result(scene) # TODO warning, now scene instead of context!
    #             else:
    #                 status_message = "(Paused, Denoiser Working ...)"
    #                 engine.tag_redraw()
    #         elif context.scene.luxcore.viewport.denoise:
    #             try:
    #                 framebuffer.start_denoiser(engine.session)
    #                 engine.tag_redraw()
    #             except Exception as error:
    #                 status_message = "Could not start denoiser: %s" % error
    # else:
    #     # Not in pause yet, keep drawing
    #     try:
    #         engine.session.UpdateStats()
    #     except RuntimeError as error:
    #         print("[Engine/Viewport] Error during UpdateStats():", error)
    #     engine.session.WaitNewFrame()
    #     framebuffer.update(engine.session, scene) # TODO warning, now scene instead of context!
    #     framebuffer.reset_denoiser()
    #     engine.tag_redraw()
    #
    # framebuffer.draw(engine, context)
    #
    # # Show formatted statistics in Blender UI
    # config = engine.session.GetRenderConfig()
    # stats = engine.session.GetStats()
    # pretty_stats = utils_render.get_pretty_stats(config, stats, scene, context)
    # engine.update_stats(pretty_stats, status_message)

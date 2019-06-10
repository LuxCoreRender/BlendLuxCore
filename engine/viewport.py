from time import time
from .. import export
from ..draw.viewport import FrameBuffer
from ..utils import render as utils_render

import bpy
from ..bin import pyluxcore
from .. import utils
from ..export import blender_object_280


def view_update(engine, context, depsgraph, changes=None):
    scene = depsgraph.scene_eval

    if engine.session is None and not engine.starting_session:
        engine.starting_session = True

        # engine.exporter = export.Exporter(scene)
        # # Note: in viewport render, the user can't cancel the
        # # export (Blender limitation), so we don't pass engine here
        # engine.session = engine.exporter.create_session(context)
        # engine.session.Start()

        # Just for mesh export testing
        scene_props = pyluxcore.Properties()
        scene_props.SetFromString("""
            scene.materials.__CLAY__.type = "matte"
            scene.materials.__CLAY__.kd = 0.5 0.5 0.5
            
            scene.lights.testlight.type = "constantinfinite"
            scene.lights.testlight.gain = 0.1 0.1 0.1
            scene.lights.testlight.visibilitymap.enable = 0
            
            scene.lights.testlight2.type = "point"
            scene.lights.testlight2.position = -2 -2 1.6
            scene.lights.testlight2.gain = 600 50 50
            """)
        from ..export import camera
        cam_props = camera.convert(None, scene, context)
        scene_props.Set(cam_props)
        filmsize = utils.calc_filmsize(scene, context)

        def start_session(engine, scene_props, filmsize):
            start = time()
            luxcore_scene = pyluxcore.Scene()

            for datablock in depsgraph.ids:
                print("checking datablock:", datablock)
                if isinstance(datablock, bpy.types.Object):
                    props = blender_object_280.convert(datablock, depsgraph, luxcore_scene, True, False)
                    if props:
                        scene_props.Set(props)

            luxcore_scene.Parse(scene_props)
            exp_time = time() - start

            config_props = pyluxcore.Properties()
            config_props.SetFromString("""
                renderengine.type = "RTPATHCPU"
                sampler.type = "RTPATHCPUSAMPLER"
                rtpathcpu.zoomphase.size = 2
                rtpathcpu.zoomphase.weight = 0
            """)
            config_props.Set(pyluxcore.Property("film.width", filmsize[0]))
            config_props.Set(pyluxcore.Property("film.height", filmsize[1]))
            t0 = time()
            renderconfig = pyluxcore.RenderConfig(config_props, luxcore_scene)
            t1 = time()
            engine.session = pyluxcore.RenderSession(renderconfig)
            t2 = time()
            print("session created")
            print("times:")
            print("export: %.3f s" % exp_time)
            print("config: %.3f s" % (t1 - t0))
            print("session: %.3f s" % (t2 - t1))

            #############################
            s = time()
            engine.session.Start()
            print("Starting session took %.3f s" % (time() - s))
            # TODO use lock when changing starting_session? probably yes
            engine.starting_session = False

        import _thread
        _thread.start_new_thread(start_session, (engine, scene_props, filmsize))

    for update in depsgraph.updates:
        datablock = update.id
        print("Datablock updated: ", datablock.name)

    if depsgraph.id_type_updated('OBJECT'):
        print("---")
        for instance in depsgraph.object_instances:
            print("Instance:", instance)

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

last_cam_str = ""

def view_draw(engine, context, depsgraph):
    scene = depsgraph.scene_eval

    if not engine.framebuffer or engine.framebuffer.needs_replacement(context, scene):
        print("new framebuffer")
        engine.framebuffer = FrameBuffer(engine, context, scene)

    if engine.session and not engine.starting_session:
        # hacky camera update
        from ..export import camera
        cam_props = camera.convert(None, scene, context)
        global last_cam_str
        new_cam_str = str(cam_props)
        if new_cam_str != last_cam_str:
            last_cam_str = new_cam_str
            luxcore_scene = engine.session.GetRenderConfig().GetScene()
            engine.session.BeginSceneEdit()
            luxcore_scene.Parse(cam_props)
            engine.session.EndSceneEdit()
            import time
            time.sleep(0.1)

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

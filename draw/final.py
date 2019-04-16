from time import time, sleep
from ..bin import pyluxcore
from .. import utils
from ..export.aovs import get_denoiser_imgpipeline_props
from ..properties.denoiser_log import DenoiserLogEntry


class AOV:
    """ Storage class for info about an Arbitrary Output Variable """
    def __init__(self, channel_count, convert_func, normalize):
        self.channel_count = channel_count
        self.convert_func = convert_func
        self.normalize = normalize


# Note: RGB_IMAGEPIPELINE and RGBA_IMAGEPIPELINE are missing here because they
# are not imported along with the other AOVs (they have a special code path)
# Note: AOVs with the default settings are not included in the aovs dictionary.
AOVS = {
    "RGBA": AOV(4, pyluxcore.ConvertFilmChannelOutput_4xFloat_To_4xFloatList, False),
    "ALPHA": AOV(1, pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
    "DEPTH": AOV(1, pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
    "DIRECT_SHADOW_MASK": AOV(1, pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
    "INDIRECT_SHADOW_MASK": AOV(1, pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
    "UV": AOV(2, pyluxcore.ConvertFilmChannelOutput_UV_to_Blender_UV, False),
    "RAYCOUNT": AOV(1, pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, True),
    "MATERIAL_ID": AOV(1, pyluxcore.ConvertFilmChannelOutput_1xUInt_To_1xFloatList, False),
    "OBJECT_ID": AOV(1, pyluxcore.ConvertFilmChannelOutput_1xUInt_To_1xFloatList, False),
    "SAMPLECOUNT": AOV(1, pyluxcore.ConvertFilmChannelOutput_1xUInt_To_1xFloatList, True),
    "CONVERGENCE": AOV(1, pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
    "NOISE": AOV(1, pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
}
DEFAULT_AOV_SETTINGS = AOV(3, pyluxcore.ConvertFilmChannelOutput_3xFloat_To_3xFloatList, False)

AOVS_WITH_ID = {"RADIANCE_GROUP", "BY_MATERIAL_ID", "BY_OBJECT_ID", "MATERIAL_ID_MASK", "OBJECT_ID_MASK"}


class FrameBufferFinal(object):
    """ FrameBuffer for final render """
    def __init__(self, scene):
        filmsize = utils.calc_filmsize(scene)
        self._width = filmsize[0]
        self._height = filmsize[1]
        self._border = utils.calc_blender_border(scene)
        pipeline = scene.camera.data.luxcore.imagepipeline
        self._transparent = pipeline.transparent_film

        if self._transparent:
            self._combined_output_type = pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
            self._convert_combined = pyluxcore.ConvertFilmChannelOutput_4xFloat_To_4xFloatList
        else:
            self._combined_output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE
            self._convert_combined = pyluxcore.ConvertFilmChannelOutput_3xFloat_To_4xFloatList

        # How long the last run of the denoiser took, in seconds
        self.denoiser_last_elapsed_time = 0
        self.denoiser_last_samples = 0

    def draw(self, engine, session, scene, render_stopped):
        active_layer_index = scene.luxcore.active_layer_index
        scene_layer = scene.render.layers[active_layer_index]

        result = engine.begin_result(0, 0, self._width, self._height, scene_layer.name)
        # Regardless of the scene render layers, the result always only contains one layer
        render_layer = result.layers[0]

        combined = render_layer.passes["Combined"]
        self._convert_combined(session.GetFilm(), self._combined_output_type, 0,
                               self._width, self._height, combined.as_pointer(), False, True)

        # Import AOVs only in final render, not in material preview mode
        if not engine.is_preview:
            for output_name, output_type in pyluxcore.FilmOutputType.names.items():
                # Check if this AOV is enabled on this render layer
                if getattr(scene_layer.luxcore.aovs, output_name.lower(), False):
                    try:
                        self._import_aov(output_name, output_type, render_layer, session, engine)
                    except RuntimeError as error:
                        print("Error on import of AOV %s: %s" % (output_name, error))

            lightgroup_pass_names = scene.luxcore.lightgroups.get_pass_names()
            for i, name in enumerate(lightgroup_pass_names):
                if i not in engine.exporter.lightgroup_cache:
                    # This light group is not used by any lights in the scene, so it was not defined
                    continue

                output_name = "RADIANCE_GROUP"
                output_type = pyluxcore.FilmOutputType.RADIANCE_GROUP
                try:
                    self._import_aov(output_name, output_type, render_layer, session, engine, True, i, name)
                except RuntimeError as error:
                    print("Error on import of Lightgroup AOV of group %s: %s" % (name, error))

            self._refresh_denoiser(engine, session, scene, render_layer, render_stopped)

        engine.end_result(result)
        # Reset the refresh button
        self._reset_button(scene.luxcore.display, "refresh")

    def _import_aov(self, output_name, output_type, render_layer, session, engine,
                    execute_imagepipeline=True, index=0, lightgroup_name=""):
        if output_name in AOVS:
            aov = AOVS[output_name]
        else:
            aov = DEFAULT_AOV_SETTINGS

        if output_name in AOVS_WITH_ID:
            # Add the index so we can differentiate between the outputs with id
            output_name += str(index)

        if output_name in engine.aov_imagepipelines:
            index = engine.aov_imagepipelines[output_name]
            output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE
            convert_func = DEFAULT_AOV_SETTINGS.convert_func
        else:
            convert_func = aov.convert_func

        # Depth needs special treatment because it's pre-defined by Blender and not uppercase
        if output_name == "DEPTH":
            pass_name = "Depth"
        elif output_name.startswith("RADIANCE_GROUP"):
            pass_name = lightgroup_name
        else:
            pass_name = output_name

        blender_pass = render_layer.passes[pass_name]

        # Convert and copy the buffer into the blender_pass.rect
        convert_func(session.GetFilm(), output_type, index,
                     self._width, self._height, blender_pass.as_pointer(),
                     aov.normalize, execute_imagepipeline)

    def _refresh_denoiser(self, engine, session, scene, render_layer, render_stopped):
        if not engine.has_denoiser():
            return

        output_name = engine.DENOISED_OUTPUT_NAME
        output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE

        # Refresh when ending the render (Esc/halt condition) or when the user presses the refresh button
        refresh_denoised = render_stopped or scene.luxcore.denoiser.refresh

        stats = engine.session.GetStats()
        samples = stats.Get("stats.renderengine.pass").GetInt()

        if render_stopped and samples == self.denoiser_last_samples:
            # No new samples, do not run the denoiser. Saves time when the user
            # cancels the render wile the denoiser is running, for example.
            print("No new samples since last denoiser run, skipping denoising.")
            refresh_denoised = False

        if refresh_denoised:
            print("Refreshing DENOISED")
            self.denoiser_last_samples = samples

            # Update the imagepipeline
            denoiser_pipeline_index = engine.aov_imagepipelines[output_name]
            denoiser_pipeline_props = get_denoiser_imgpipeline_props(None, scene, denoiser_pipeline_index)
            session.Parse(denoiser_pipeline_props)

            was_paused = session.IsInPause()
            if not was_paused:
                session.Pause()

            try:
                # Start the denoiser imagepipeline asynchronous (so it does not lock Blender)
                session.GetFilm().AsyncExecuteImagePipeline(denoiser_pipeline_index)
                start = time()

                while not session.GetFilm().HasDoneAsyncExecuteImagePipeline():
                    elapsed = round(time() - start)
                    if self.denoiser_last_elapsed_time:
                        last = "%d s" % self.denoiser_last_elapsed_time
                    else:
                        last = "unkown"
                    engine.update_stats("Denoising...", "Elapsed: {} s (last: {})".format(elapsed, last))
                    sleep(1)

                self.denoiser_last_elapsed_time = round(time() - start)

                # Import the denoised image without executing the imagepipeline again
                self._import_aov(output_name, output_type, render_layer, session, engine,
                                 execute_imagepipeline=False)
            except RuntimeError as error:
                print("Error on import of denoised result: %s" % error)

            if not was_paused and session.IsInPause():
                session.Resume()

            # Add denoiser log entry
            rendered_time = stats.Get("stats.renderengine.time").GetFloat()
            settings = scene.luxcore.denoiser
            elapsed = self.denoiser_last_elapsed_time
            log_entry = DenoiserLogEntry(samples, rendered_time, elapsed, settings)
            scene.luxcore.denoiser_log.add(log_entry)

            # Reset the refresh button
            self._reset_button(scene.luxcore.denoiser, "refresh")
            engine.update_stats("Denoiser Done", "Elapsed: {} s".format(elapsed))
        else:
            # If we do not write something into the result, the image will be black.
            # So we re-use the result from the last denoiser run.
            self._import_aov(output_name, output_type, render_layer, session, engine,
                             execute_imagepipeline=False)

    def _reset_button(self, data, property_name):
        if getattr(data, property_name):
            try:
                setattr(data, property_name, False)
            except AttributeError as error:
                # Sometimes Blender raises this exception, not sure when and why:
                # AttributeError: Writing to ID classes in this context is not allowed:
                # Scene, Scene datablock, error setting LuxCoreDisplaySettings.refresh
                print(error)

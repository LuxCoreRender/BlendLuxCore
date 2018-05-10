from bgl import *  # Nah I'm not typing them all out
import array
from time import time
from ..bin import pyluxcore
from .. import utils
from ..export.aovs import get_denoiser_imgpipeline_props


class AOV:
    """ Storage class for info about an Arbitrary Output Variable """
    def __init__(self, channel_count, array_type, convert_func, normalize):
        self.channel_count = channel_count
        # array_type is the type of the intermediate array.
        # In the end, everything is converted to float for Blender.
        self.array_type = array_type
        self.convert_func = convert_func
        self.normalize = normalize


# Note: RGB_IMAGEPIPELINE and RGBA_IMAGEPIPELINE are missing here because they
# are not imported along with the other AOVs (they have a special code path)
# Note: AOVs with the default settings are not included in the aovs dictionary.
AOVS = {
    "RGBA": AOV(4, "f", pyluxcore.ConvertFilmChannelOutput_4xFloat_To_4xFloatList, False),
    "ALPHA": AOV(1, "f", pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
    "DEPTH": AOV(1, "f", pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
    "DIRECT_SHADOW_MASK": AOV(1, "f", pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
    "INDIRECT_SHADOW_MASK": AOV(1, "f", pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
    "UV": AOV(2, "f", pyluxcore.ConvertFilmChannelOutput_UV_to_Blender_UV, False),
    "RAYCOUNT": AOV(1, "f", pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, True),
    "MATERIAL_ID": AOV(1, "I", pyluxcore.ConvertFilmChannelOutput_1xUInt_To_1xFloatList, False),
    "OBJECT_ID": AOV(1, "I", pyluxcore.ConvertFilmChannelOutput_1xUInt_To_1xFloatList, False),
    "SAMPLECOUNT": AOV(1, "I", pyluxcore.ConvertFilmChannelOutput_1xUInt_To_1xFloatList, True),
    "CONVERGENCE": AOV(1, "f", pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
}
DEFAULT_AOV_SETTINGS = AOV(3, "f", pyluxcore.ConvertFilmChannelOutput_3xFloat_To_3xFloatList, False)

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

        # This dict is only used by the denoiser
        self.aov_buffers = {}

        self.last_denoiser_refresh = 0

    def draw(self, engine, session, scene, render_stopped):
        active_layer_index = scene.luxcore.active_layer_index
        scene_layer = scene.render.layers[active_layer_index]

        # Reset the refresh button
        scene.luxcore.display.refresh = False

        result = engine.begin_result(0, 0, self._width, self._height, scene_layer.name)
        # Regardless of the scene render layers, the result always only contains one layer
        render_layer = result.layers[0]

        combined = render_layer.passes["Combined"]
        self._convert_combined(session.GetFilm(), self._combined_output_type, 0,
                               self._width, self._height, combined.as_pointer(), False)

        # Import AOVs only in final render, not in material preview mode
        if not engine.is_preview:
            for output_name, output_type in pyluxcore.FilmOutputType.names.items():
                # Check if AOV is enabled by user
                if getattr(scene_layer.luxcore.aovs, output_name.lower(), False):
                    try:
                        self._import_aov(output_name, output_type, render_layer, session, engine)
                    except RuntimeError as error:
                        print("Error on import of AOV %s: %s" % (output_name, error))

            lightgroup_pass_names = scene.luxcore.lightgroups.get_pass_names()
            for i, name in enumerate(lightgroup_pass_names):
                if i not in engine.exporter.lightgroup_cache:
                    # This light group is not used by any lights int the scene, so it was not defined
                    continue

                output_name = "RADIANCE_GROUP"
                output_type = pyluxcore.FilmOutputType.RADIANCE_GROUP
                try:
                    self._import_aov(output_name, output_type, render_layer, session, engine, i, name)
                except RuntimeError as error:
                    print("Error on import of Lightgroup AOV of group %s: %s" % (name, error))

            self._refresh_denoiser(engine, session, scene, render_layer, render_stopped)

        engine.end_result(result)

    def _import_aov(self, output_name, output_type, render_layer, session, engine, index=0, lightgroup_name=""):
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
                     aov.normalize)

    def _refresh_denoiser(self, engine, session, scene, render_layer, render_stopped):
        # Denoiser result
        output_name = "DENOISED"
        if output_name not in engine.aov_imagepipelines:
            # The denoiser is not enabled
            return

        # Refresh when ending the render (Esc/halt condition) or when the user presses the refresh button
        refresh_denoised = render_stopped or scene.luxcore.denoiser.refresh

        # Also check if a few seconds have passed since the last refresh
        # ended, to prevent the user accidentally triggering another refresh
        if refresh_denoised and time() - self.last_denoiser_refresh > 3:
            print("Refreshing DENOISED")
            # Reset the refresh button
            scene.luxcore.denoiser.refresh = False
            # Update the imagepipeline
            denoiser_pipeline_index = engine.aov_imagepipelines[output_name]
            denoiser_pipeline_props = get_denoiser_imgpipeline_props(None, scene, denoiser_pipeline_index)
            session.Parse(denoiser_pipeline_props)

            # TODO: What about alpha (RGBA)?
            output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE

            was_paused = session.IsInPause()
            if not was_paused:
                session.Pause()

            try:
                self._import_aov(output_name, output_type, render_layer, session, engine)
            except RuntimeError as error:
                print("Error on import of denoised result: %s" % error)

            if not was_paused and session.IsInPause():
                session.Resume()

            self.last_denoiser_refresh = time()
        elif output_name in self.aov_buffers:
            print("Reusing buffer")
            # If we do not write something into the result, the image will be black.
            # So we re-use the result from the last denoiser run.
            buffer = self.aov_buffers[output_name]
            blender_pass = render_layer.passes[output_name]
            # TODO make this faster either in C++ or Python
            blender_pass.rect = [(buffer[i], buffer[i + 1], buffer[i + 2]) for i in range(0, len(buffer), 3)]

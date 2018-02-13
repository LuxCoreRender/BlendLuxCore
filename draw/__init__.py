import bgl
from bgl import *  # Nah I'm not typing them all out
import math
import array
from ..bin import pyluxcore
from .. import utils


def draw_quad(offset_x, offset_y, width, height):
    glBegin(GL_QUADS)

    # 0, 0 (top left)
    glTexCoord2f(0, 0)
    glVertex2f(offset_x, offset_y)

    # 1, 0 (top right)
    glTexCoord2f(1, 0)
    glVertex2f(offset_x + width, offset_y)

    # 1, 1 (bottom right)
    glTexCoord2f(1, 1)
    glVertex2f(offset_x + width, offset_y + height)

    # 0, 1 (bottom left)
    glTexCoord2f(0, 1)
    glVertex2f(offset_x, offset_y + height)

    glEnd()


class FrameBuffer(object):
    """ FrameBuffer used for viewport render """

    def __init__(self, context):
        filmsize = utils.calc_filmsize(context.scene, context)
        self._width = filmsize[0]
        self._height = filmsize[1]
        self._border = utils.calc_blender_border(context.scene, context)

        if context.scene.camera:
            pipeline = context.scene.camera.data.luxcore.imagepipeline
            self._transparent = pipeline.transparent_film
        else:
            self._transparent = False

        if self._transparent:
            bufferdepth = 4
            self._buffertype = GL_RGBA
            self._output_type = pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
        else:
            bufferdepth = 3
            self._buffertype = GL_RGB
            self._output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE

        self.buffer = Buffer(GL_FLOAT, [self._width * self._height * bufferdepth])

        # Create texture
        self.texture = Buffer(GL_INT, 1)
        glGenTextures(1, self.texture)
        self.texture_id = self.texture[0]

    def update(self, luxcore_session):
        luxcore_session.GetFilm().GetOutputFloat(self._output_type, self.buffer)

        # update texture
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        if self._transparent:
            mode = GL_RGBA
        else:
            mode = GL_RGB
        glTexImage2D(GL_TEXTURE_2D, 0, mode, self._width, self._height, 0, mode,
                     GL_FLOAT, self.buffer)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def draw(self, region_size, view_camera_offset, view_camera_zoom, engine, context):
        if self._transparent:
            glEnable(GL_BLEND)

        zoom = 0.25 * ((math.sqrt(2) + view_camera_zoom / 50) ** 2)
        offset_x, offset_y = self._calc_offset(context, region_size, view_camera_offset, zoom)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_COLOR_MATERIAL)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        if engine.support_display_space_shader(context.scene):
            # This is the fragment shader that applies Blender color management
            engine.bind_display_space_shader(context.scene)

        draw_quad(offset_x, offset_y, self._width, self._height)

        if engine.support_display_space_shader(context.scene):
            engine.unbind_display_space_shader()

        glDisable(GL_COLOR_MATERIAL)
        glDisable(GL_TEXTURE_2D)

        err = glGetError()
        if err != GL_NO_ERROR:
            print("GL Error: %s\n" % (gluErrorString(err)))

        if self._transparent:
            glDisable(GL_BLEND)

    def _calc_offset(self, context, region_size, view_camera_offset, zoom):
        width_raw, height_raw = region_size
        border_min_x, border_max_x, border_min_y, border_max_y = self._border

        if context.region_data.view_perspective == "CAMERA" and context.scene.render.use_border:
            # Offset is only needed if viewport is in camera mode and uses border rendering
            aspect_x, aspect_y = utils.calc_aspect(context.scene.render.resolution_x, context.scene.render.resolution_y)

            base = 0.5 * zoom * max(width_raw, height_raw)
           
            offset_x = (0.5 - 2*zoom * view_camera_offset[0])*width_raw  - aspect_x*base + border_min_x*2*aspect_x*base
            offset_y = (0.5 - 2*zoom * view_camera_offset[1])*height_raw - aspect_y*base + border_min_y*2*aspect_y*base
            
        else:
            offset_x = width_raw * border_min_x + 1
            offset_y = height_raw * border_min_y + 1

        # offset_x, offset_y are in pixels
        return int(offset_x), int(offset_y)

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
            bufferdepth = 4
            self._output_type = pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
            self._convert_combined = pyluxcore.ConvertFilmChannelOutput_4xFloat_To_4xFloatList
        else:
            bufferdepth = 3
            self._output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE
            self._convert_combined = pyluxcore.ConvertFilmChannelOutput_3xFloat_To_4xFloatList

        self.buffer = array.array("f", [0.0] * (self._width * self._height * bufferdepth))

    def draw(self, engine, session, scene):
        session.GetFilm().GetOutputFloat(self._output_type, self.buffer)
        result = engine.begin_result(0, 0, self._width, self._height)
        layer = result.layers[0]

        combined = layer.passes["Combined"]
        combined.rect = self._convert_combined(self._width, self._height, self.buffer, False)

        # if aovs.depth:
        #     arrayDepth = 1
        #     channel_buffer = array.array("f", [0] * (self._width * self._height * arrayDepth))
        #     session.GetFilm().GetOutputFloat(pyluxcore.FilmOutputType.DEPTH, channel_buffer)
        #
        #     depth = layer.passes["Depth"]
        #     depth.rect = pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList(self._width, self._height, channel_buffer, False)
        #
        # if aovs.samplecount:
        #     arrayDepth = 1
        #     channel_buffer = array.array("I", [0] * (self._width * self._height * arrayDepth))
        #     session.GetFilm().GetOutputUInt(pyluxcore.FilmOutputType.SAMPLECOUNT, channel_buffer)
        #
        #     samplecount = layer.passes["Samplecount"]
        #     samplecount.rect = pyluxcore.ConvertFilmChannelOutput_1xUInt_To_1xFloatList(self._width, self._height, channel_buffer, True)

        # # Default count is 3, those are not included here
        # channel_count = {
        #     "DEPTH": 1,
        #     "SAMPLECOUNT": 1,
        # }
        #
        # # Default type is "f", those are not included here
        # array_types = {
        #     "SAMPLECOUNT": "I",
        # }
        #
        # convert_func = {
        #     "DEPTH": pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList,
        #     "SAMPLECOUNT": pyluxcore.ConvertFilmChannelOutput_1xUInt_To_1xFloatList,
        # }
        #
        # normalize_channels = {
        #     "SAMPLECOUNT"
        # }

        aovs = {
            "DEPTH": AOV(1, "f", pyluxcore.ConvertFilmChannelOutput_1xFloat_To_1xFloatList, False),
            "SAMPLECOUNT": AOV(1, "I", pyluxcore.ConvertFilmChannelOutput_1xUInt_To_1xFloatList, True),
        }

        for output_name, output_type in pyluxcore.FilmOutputType.names.items():
            if getattr(scene.luxcore.aovs, output_name.lower(), False):
                # AOV is enabled by user
                # if output_name in channel_count.keys():
                #     array_depth = channel_count[output_name]
                # else:
                #     # Use default channel count
                #     array_depth = 3
                #
                # if output_name in array_types.keys():
                #     array_type = array_types[output_name]
                # else:
                #     array_type = "f"
                #
                # buffer = array.array(array_type, [0] * (self._width * self._height * array_depth))
                #
                # # Fill the buffer
                # if array_type == "I":
                #     session.GetFilm().GetOutputUInt(output_type, buffer)
                # else:
                #     session.GetFilm().GetOutputFloat(output_type, buffer)
                #
                # normalize = output_name in normalize_channels

                # blender_pass = layer.passes[output_name.title()]
                # blender_pass.rect = convert_func[output_name](self._width, self._height, buffer, normalize)

                aov = aovs[output_name]
                w = self._width
                h = self._height

                buffer = array.array(aov.array_type, [0] * (w * h * aov.channel_count))

                # Fill the buffer
                if aov.array_type == "I":
                    session.GetFilm().GetOutputUInt(output_type, buffer)
                else:
                    session.GetFilm().GetOutputFloat(output_type, buffer)

                blender_pass = layer.passes[output_name.title()]
                blender_pass.rect = aov.convert_func(w, h, buffer, aov.normalize)

        engine.end_result(result)


class AOV:
    def __init__(self, channel_count, array_type, convert_func, normalize):
        self.channel_count = channel_count
        self.array_type = array_type
        self.convert_func = convert_func
        self.normalize = normalize

# AOVS = {
#     "DEPTH": AOV(pyluxcore.FilmOutputType.DEPTH, 1),
# }

# d = {key: value for (key, value) in iterable}
#
#
#
# AOVS = {
#     str()
# }
import bgl
from bgl import *  # Nah I'm not typing them all out
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

        transparent = False  # TODO
        if transparent:
            bufferdepth = 4
            self._buffertype = GL_RGBA
            self._output_type = pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
        else:
            bufferdepth = 3
            self._buffertype = GL_RGB
            self._output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE

        self.buffer = Buffer(GL_FLOAT, [self._width * self._height * bufferdepth])
        self._transparent = transparent

        # Create texture
        self.texture = Buffer(GL_INT, 1)
        glGenTextures(1, self.texture)
        self.texture_id = self.texture[0]

    def update(self, luxcore_session):
        luxcore_session.GetFilm().GetOutputFloat(self._output_type, self.buffer)

        # update texture
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self._width, self._height, 0, GL_RGB,
                     GL_FLOAT, self.buffer)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def draw(self, region_size, view_camera_offset, engine, context):
        if self._transparent:
            glEnable(GL_BLEND)

        offset_x, offset_y = self._calc_offset(region_size, view_camera_offset)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_COLOR_MATERIAL)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        if engine.support_display_space_shader(context.scene):
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

    def _calc_offset(self, region_size, view_camera_offset):
        # TODO: view_camera_offset, to get correct draw position in camera viewport mode
        width_raw, height_raw = region_size
        border_min_x, border_max_x, border_min_y, border_max_y = self._border

        # TODO: not sure about the +1, needs further testing to see if rounding is better
        offset_x = width_raw * border_min_x + 1
        offset_y = height_raw * border_min_y + 1

        #view_camera_offset = [(v + 1) / 2 for v in view_camera_offset]
        # view_cam_shift_x = width_raw * view_camera_offset[0]
        # view_cam_shift_y = height_raw * view_camera_offset[1]

        # xaspect, yaspect = utils.calc_aspect(width_raw, height_raw)
        # offset_x = (view_camera_offset[0] * xaspect * 2) * width_raw
        # offset_y = (view_camera_offset[1] * yaspect * 2) * height_raw
        #print("offsets:", offset_x, offset_y)


        # view_camera_offset is completely weird (range -1..1, mirrored axis),
        # bring it into 0..1 range with 0,0 in lower left corner and 1,1 in upper right corner
        # view_camera_offset[0] = 1 - (view_camera_offset[0] + 1) / 2
        # view_camera_offset[1] = 1 - (view_camera_offset[1] + 1) / 2
        # offset_x = view_camera_offset[0] * width_raw
        # offset_y = view_camera_offset[1] * height_raw
        # print("offsets:", offset_x, offset_y)


        # offset_x, offset_y are in pixels
        return int(offset_x), int(offset_y)


class FrameBufferFinal(object):
    """ FrameBuffer for final render """
    def __init__(self, scene):
        filmsize = utils.calc_filmsize(scene)
        self._width = filmsize[0]
        self._height = filmsize[1]
        self._border = utils.calc_blender_border(scene)

        transparent = False  # TODO
        if transparent:
            bufferdepth = 4
            self._output_type = pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
            self._convert_func = pyluxcore.ConvertFilmChannelOutput_4xFloat_To_4xFloatList
        else:
            bufferdepth = 3
            self._output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE
            self._convert_func = pyluxcore.ConvertFilmChannelOutput_3xFloat_To_3xFloatList

        self.buffer = array.array("f", [0.0] * (self._width * self._height * bufferdepth))
        self._transparent = transparent

    def draw(self, render_engine, session):
        session.GetFilm().GetOutputFloat(self._output_type, self.buffer)
        result = render_engine.begin_result(0, 0, self._width, self._height)
        layer = result.layers[0].passes[0]

        if self._transparent:
            # Need the extra "False" because this function has an additional "normalize" argument
            layer.rect = self._convert_func(self._width, self._height, self.buffer, False)
        else:
            layer.rect = self._convert_func(self._width, self._height, self.buffer)

        render_engine.end_result(result)
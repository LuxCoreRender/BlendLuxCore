import bgl
from ..bin import pyluxcore
from .. import utils


class FrameBuffer(object):
    def __init__(self, context):
        filmsize = utils.calc_filmsize(context.scene, context)
        self._width = filmsize[0]
        self._height = filmsize[1]
        self._border = utils.calc_blender_border(context.scene, context)

        transparent = False  # TODO
        if transparent:
            bufferdepth = 4
            self._buffertype = bgl.GL_RGBA
            self._output_type = pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
        else:
            bufferdepth = 3
            self._buffertype = bgl.GL_RGB
            self._output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE

        self.buffer = bgl.Buffer(bgl.GL_FLOAT, [self._width * self._height * bufferdepth])
        self._transparent = transparent

    def update(self, luxcore_session):
        luxcore_session.GetFilm().GetOutputFloat(self._output_type, self.buffer)

    def draw(self, region_size, view_camera_offset):
        if self._transparent:
            bgl.glEnable(bgl.GL_BLEND)

        offset_x, offset_y = self._calc_offset(region_size, view_camera_offset)

        bgl.glRasterPos2i(offset_x, offset_y)
        bgl.glDrawPixels(self._width, self._height, self._buffertype, bgl.GL_FLOAT, self.buffer)

        if self._transparent:
            bgl.glDisable(bgl.GL_BLEND)

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
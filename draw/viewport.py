from bgl import *  # Nah I'm not typing them all out
import math
import os
import numpy
import subprocess
from ..bin import pyluxcore
from .. import utils
from ..utils import pfm


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

        if utils.is_valid_camera(context.scene.camera):
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

        # Denoiser
        current_dir = os.path.dirname(os.path.realpath(__file__))
        framebuffer_id = str(id(self))
        self._noisy_file_path = os.path.join(current_dir, framebuffer_id + "_noisy.pfm")
        self._albedo_file_path = os.path.join(current_dir, framebuffer_id + "_albedo.pfm")
        self._normal_file_path = os.path.join(current_dir, framebuffer_id + "_normal.pfm")
        self._denoised_file_path = os.path.join(current_dir, framebuffer_id + "_denoised.pfm")
        self._denoiser_path = os.path.join(os.path.dirname(current_dir), "bin", "denoise.exe")
        self._denoiser_process = None

    def __del__(self):
        # TODO make sure this is called, currently it's not reliable
        print("Cleaning up denoiser files")
        if os.path.exists(self._noisy_file_path):
            os.remove(self._noisy_file_path)
        if os.path.exists(self._denoised_file_path):
            os.remove(self._denoised_file_path)

    def update(self, luxcore_session, context):
        luxcore_session.GetFilm().GetOutputFloat(self._output_type, self.buffer)
        self._update_texture(context)

    def _save_denoiser_AOV(self, luxcore_session, film_output_type, path):
        # Bufferdepth always 3 because denoiser can't handle alpha anyway (maybe copy over alpha channel in the future)
        np_buffer = numpy.zeros((self._height, self._width, 3), dtype="float32")
        luxcore_session.GetFilm().GetOutputFloat(film_output_type, np_buffer)
        # TODO use tempfile.SpooledTemporaryFile to avoid saving the file to disk (for output as well, if possible)
        with open(path, "wb") as f:
            # TODO handle exceptions (e.g. no write permissions)
            utils.pfm.save_pfm(f, np_buffer)

    def start_denoiser(self, luxcore_session):
        self._save_denoiser_AOV(luxcore_session, pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE, self._noisy_file_path)
        self._save_denoiser_AOV(luxcore_session, pyluxcore.FilmOutputType.ALBEDO, self._albedo_file_path)
        self._save_denoiser_AOV(luxcore_session, pyluxcore.FilmOutputType.AVG_SHADING_NORMAL, self._normal_file_path)

        args = [
            self._denoiser_path,
            "-hdr", self._noisy_file_path,
            "-alb", self._albedo_file_path,
            "-nrm", self._normal_file_path,
            "-o", self._denoised_file_path,
        ]
        self._denoiser_process = subprocess.Popen(args)
        return True

    def is_denoiser_active(self):
        return self._denoiser_process is not None

    def is_denoiser_done(self):
        return self._denoiser_process.poll() is not None

    def load_denoiser_result(self, context):
        self._denoiser_process = None
        with open(self._denoised_file_path, "rb") as f:
            # TODO handle exceptions
            data, scale = utils.pfm.load_pfm(f, as_flat_list=True)
        self.buffer[:] = data
        self._update_texture(context)

    def reset_denoiser(self):
        """ Denoiser was not started yet or the user has triggered an update """
        if self._denoiser_process:
            print("killing denoiser")
            self._denoiser_process.terminate()
            self._denoiser_process.communicate()
            self._denoiser_process = None

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

        pixel_size = int(context.scene.luxcore.viewport.pixel_size)
        draw_quad(offset_x, offset_y, self._width * pixel_size, self._height * pixel_size)

        if engine.support_display_space_shader(context.scene):
            engine.unbind_display_space_shader()

        glDisable(GL_COLOR_MATERIAL)
        glDisable(GL_TEXTURE_2D)

        err = glGetError()
        if err != GL_NO_ERROR:
            print("GL Error:", err)

        if self._transparent:
            glDisable(GL_BLEND)

    def _update_texture(self, context):
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        if self._transparent:
            gl_format = GL_RGBA
            internal_format = GL_RGBA32F
        else:
            gl_format = GL_RGB
            internal_format = GL_RGB32F
        glTexImage2D(GL_TEXTURE_2D, 0, internal_format, self._width, self._height,
                     0, gl_format, GL_FLOAT, self.buffer)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        mag_filter = GL_NEAREST if context.scene.luxcore.viewport.mag_filter == "NEAREST" else GL_LINEAR
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, mag_filter)

    def _calc_offset(self, context, region_size, view_camera_offset, zoom):
        render = context.scene.render
        region_width, region_height = region_size
        border_min_x, border_max_x, border_min_y, border_max_y = self._border

        if context.region_data.view_perspective == "CAMERA" and render.use_border:
            # Offset is only needed if viewport is in camera mode and uses border rendering
            sensor_fit = context.scene.camera.data.sensor_fit

            aspectratio, aspect_x, aspect_y = utils.calc_aspect(
                render.resolution_x * render.pixel_aspect_x,
                render.resolution_y * render.pixel_aspect_y,
                sensor_fit)

            base = 0.5 * zoom
            if sensor_fit == "AUTO":
                base *= max(region_width, region_height)
            elif sensor_fit == "HORIZONTAL":
                base *= region_width
            elif sensor_fit == "VERTICAL":
                base *= region_height

            offset_x = self._cam_border_offset(aspect_x, base, border_min_x, region_width, view_camera_offset[0], zoom)
            offset_y = self._cam_border_offset(aspect_y, base, border_min_y, region_height, view_camera_offset[1], zoom)

        else:
            offset_x = region_width * border_min_x + 1
            offset_y = region_height * border_min_y + 1

        # offset_x, offset_y are in pixels
        return int(offset_x), int(offset_y)

    def _cam_border_offset(self, aspect, base, border_min, region_width, view_camera_offset, zoom):
        return (0.5 - 2 * zoom * view_camera_offset) * region_width + aspect * base * (2 * border_min - 1)

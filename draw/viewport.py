from bgl import *  # Nah I'm not typing them all out
import math
from ..bin import pyluxcore
from .. import utils

import subprocess
import tempfile
import bpy
import os
from bpy_extras.image_utils import load_image


class OptixTempFileManager:
    files = set()

    @classmethod
    def track(cls, path):
        cls.files.add(path)

    @classmethod
    def generate_filename(cls, framebuffer_id, suffix="", extension=".png"):
        name = "optix_" + str(framebuffer_id) + suffix + extension
        filepath = os.path.join(tempfile.gettempdir(), name)
        return filepath

    @classmethod
    def cleanup(cls):
        for path in cls.files:
            print("[Optix TempFiles] Deleting temporary file:", path)
            try:
                os.remove(path)
            except FileNotFoundError as err:
                print(err)

        cls.files.clear()


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

        self.optix_result = None
        self.optix_result_path = None
        self._optix_process = None

    def start_optix(self, luxcore_session, context):
        # Can't gl_load a .exr
        ext = ".png"
        framebuffer_id = id(self)

        raw_path = OptixTempFileManager.generate_filename(framebuffer_id, "_raw", ext)
        result_path = OptixTempFileManager.generate_filename(framebuffer_id, "_result", ext)
        self.optix_result_path = result_path

        luxcore_session.GetFilm().SaveOutput(raw_path, self._output_type, pyluxcore.Properties())
        OptixTempFileManager.track(raw_path)
        # Also track LuxCore's backup file in case it's created
        OptixTempFileManager.track(raw_path + ".bak")

        denoiser_path = r"C:\Users\Simon\AppData\Roaming\Blender Foundation\Blender\2.79\scripts\addons\Denosier_v2.1\Denoiser.exe"
        args = [denoiser_path, '-i', raw_path, "-o", result_path]
        self._optix_process = subprocess.Popen(args)

    def optix_process_active(self):
        return self._optix_process is not None

    def optix_done(self):
        return self._optix_process.poll() is not None

    def load_optix_result(self):
        self._optix_process = None

        OptixTempFileManager.track(self.optix_result_path)
        load_image(self.optix_result_path, check_existing=True, force_reload=True)
        image_name = os.path.basename(self.optix_result_path)

        self.optix_result = bpy.data.images[image_name]
        self.optix_result.gl_free()
        self.optix_result.gl_load(GL_NEAREST, GL_NEAREST)

    def reset_optix(self):
        # Optix was not started yet or the user has triggered an update
        if self.optix_result_path and os.path.exists(self.optix_result_path):
            os.remove(self.optix_result_path)
        self.optix_result = None
        self.optix_result_path = None

        if self._optix_process:
            print("killing optix")
            self._optix_process.terminate()
            self._optix_process.communicate()
            self._optix_process = None

    def update(self, luxcore_session, context):
        luxcore_session.GetFilm().GetOutputFloat(self._output_type, self.buffer)

        # update texture
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

    def draw(self, region_size, view_camera_offset, view_camera_zoom, engine, context):
        if self._transparent:
            glEnable(GL_BLEND)

        zoom = 0.25 * ((math.sqrt(2) + view_camera_zoom / 50) ** 2)
        offset_x, offset_y = self._calc_offset(context, region_size, view_camera_offset, zoom)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_COLOR_MATERIAL)
        if self.optix_result:
            glBindTexture(GL_TEXTURE_2D, self.optix_result.bindcode[0])
        else:
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

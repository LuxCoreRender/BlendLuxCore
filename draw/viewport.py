import bgl
import math
import os
import platform
import numpy
import subprocess
import tempfile
from ..bin import pyluxcore
from .. import utils
from ..utils import pfm

NULL = 0


class TempfileManager:
    _paths = {}

    @classmethod
    def track(cls, key, path):
        try:
            cls._paths[key].add(path)
        except KeyError:
            cls._paths[key] = {path}

    @classmethod
    def delete_files(cls, key):
        if key not in cls._paths:
            return
        for path in cls._paths[key]:
            if os.path.exists(path):
                os.remove(path)

    @classmethod
    def cleanup(cls):
        for path_set in cls._paths.values():
            for path in path_set:
                if os.path.exists(path):
                    os.remove(path)
        cls._paths.clear()


class FrameBuffer(object):
    """ FrameBuffer used for viewport render """

    def __init__(self, engine, context, scene):
        filmsize = utils.calc_filmsize(scene, context)
        self._width, self._height = filmsize
        self._border = utils.calc_blender_border(scene, context)
        self._offset_x, self._offset_y = self._calc_offset(context, scene, self._border)
        self._pixel_size = int(scene.luxcore.viewport.pixel_size)

        if utils.is_valid_camera(scene.camera) and not utils.in_material_shading_mode(context):
            pipeline = scene.camera.data.luxcore.imagepipeline
            self._transparent = pipeline.transparent_film
        else:
            self._transparent = False

        if self._transparent:
            bufferdepth = 4
            self._buffertype = bgl.GL_RGBA
            self._output_type = pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
        else:
            bufferdepth = 3
            self._buffertype = bgl.GL_RGB
            self._output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE

        self.buffer = bgl.Buffer(bgl.GL_FLOAT, [self._width * self._height * bufferdepth])
        self._init_opengl(engine, scene)

        # Denoiser
        self._noisy_file_path = self._make_denoiser_filepath("noisy")
        self._albedo_file_path = self._make_denoiser_filepath("albedo")
        self._normal_file_path = self._make_denoiser_filepath("normal")
        self._denoised_file_path = self._make_denoiser_filepath("denoised")
        current_dir = os.path.dirname(os.path.realpath(__file__))
        self._denoiser_path = os.path.join(os.path.dirname(current_dir), "bin", "denoise")
        if platform.system() == "Windows":
            self._denoiser_path += ".exe"
        self._denoiser_process = None
        self.denoiser_result_cached = False

    def _init_opengl(self, engine, scene):
        # Create texture
        self.texture = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenTextures(1, self.texture)
        self.texture_id = self.texture[0]

        # Bind shader that converts from scene linear to display space,
        # use the scene's color management settings.
        engine.bind_display_space_shader(scene)
        shader_program = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGetIntegerv(bgl.GL_CURRENT_PROGRAM, shader_program)

        # Generate vertex array
        self.vertex_array = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenVertexArrays(1, self.vertex_array)
        bgl.glBindVertexArray(self.vertex_array[0])

        texturecoord_location = bgl.glGetAttribLocation(shader_program[0], "texCoord")
        position_location = bgl.glGetAttribLocation(shader_program[0], "pos")

        bgl.glEnableVertexAttribArray(texturecoord_location)
        bgl.glEnableVertexAttribArray(position_location)

        # Generate geometry buffers for drawing textured quad
        width = self._width * self._pixel_size
        height = self._height * self._pixel_size
        position = [
            self._offset_x, self._offset_y,
            self._offset_x + width, self._offset_y,
            self._offset_x + width, self._offset_y + height,
            self._offset_x, self._offset_y + height
        ]
        position = bgl.Buffer(bgl.GL_FLOAT, len(position), position)
        texcoord = [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
        texcoord = bgl.Buffer(bgl.GL_FLOAT, len(texcoord), texcoord)

        self.vertex_buffer = bgl.Buffer(bgl.GL_INT, 2)

        bgl.glGenBuffers(2, self.vertex_buffer)
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vertex_buffer[0])
        bgl.glBufferData(bgl.GL_ARRAY_BUFFER, 32, position, bgl.GL_STATIC_DRAW)
        bgl.glVertexAttribPointer(position_location, 2, bgl.GL_FLOAT, bgl.GL_FALSE, 0, None)

        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vertex_buffer[1])
        bgl.glBufferData(bgl.GL_ARRAY_BUFFER, 32, texcoord, bgl.GL_STATIC_DRAW)
        bgl.glVertexAttribPointer(texturecoord_location, 2, bgl.GL_FLOAT, bgl.GL_FALSE, 0, None)

        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, NULL)
        bgl.glBindVertexArray(NULL)
        engine.unbind_display_space_shader()

    def __del__(self):
        bgl.glDeleteBuffers(2, self.vertex_buffer)
        bgl.glDeleteVertexArrays(1, self.vertex_array)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, 0)
        bgl.glDeleteTextures(1, self.texture)

    def needs_replacement(self, context, scene):
        if (self._width, self._height) != utils.calc_filmsize(scene, context):
            return True
        valid_cam = utils.is_valid_camera(scene.camera)
        if valid_cam:
            if self._transparent != scene.camera.data.luxcore.imagepipeline.transparent_film:
                return True
        elif self._transparent:
            # By default (if no camera is available), the film is not transparent
            return True
        new_border = utils.calc_blender_border(scene, context)
        if self._border != new_border:
            return True
        if (self._offset_x, self._offset_y) != self._calc_offset(context, scene, new_border):
            return True
        if self._pixel_size != int(scene.luxcore.viewport.pixel_size):
            return True
        return False

    def _make_denoiser_filepath(self, name):
        return os.path.join(tempfile.gettempdir(), str(id(self)) + "_" + name + ".pfm")

    def _save_denoiser_AOV(self, luxcore_session, film_output_type, path):
        # Bufferdepth always 3 because denoiser can't handle alpha anyway (maybe copy over alpha channel in the future)
        np_buffer = numpy.zeros((self._height, self._width, 3), dtype="float32")
        luxcore_session.GetFilm().GetOutputFloat(film_output_type, np_buffer)
        TempfileManager.track(id(self), path)
        with open(path, "w+b") as f:
            utils.pfm.save_pfm(f, np_buffer)

    def start_denoiser(self, luxcore_session):
        if not os.path.exists(self._denoiser_path):
            raise Exception("Binary not found. Download it from "
                            "https://github.com/OpenImageDenoise/oidn/releases")
        if self._transparent:
            # TODO: enable ALPHA AOV and use it in case of transparent film
            raise Exception("Does not work with transparent film yet")

        self._save_denoiser_AOV(luxcore_session, pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE, self._noisy_file_path)
        self._save_denoiser_AOV(luxcore_session, pyluxcore.FilmOutputType.ALBEDO, self._albedo_file_path)
        self._save_denoiser_AOV(luxcore_session, pyluxcore.FilmOutputType.AVG_SHADING_NORMAL, self._normal_file_path)
        TempfileManager.track(id(self), self._denoised_file_path)

        args = [
            self._denoiser_path,
            "-hdr", self._noisy_file_path,
            "-alb", self._albedo_file_path,
            "-nrm", self._normal_file_path,
            "-o", self._denoised_file_path,
        ]
        self._denoiser_process = subprocess.Popen(args)

    def is_denoiser_active(self):
        return self._denoiser_process is not None

    def is_denoiser_done(self):
        return self._denoiser_process.poll() is not None

    def load_denoiser_result(self, scene):
        self._denoiser_process = None
        try:
            with open(self._denoised_file_path, "rb") as f:
                data, scale = utils.pfm.load_pfm(f, as_flat_list=True)
            TempfileManager.delete_files(id(self))
        except FileNotFoundError:
            TempfileManager.delete_files(id(self))
            raise Exception("Denoising failed, check console for details")

        self.buffer[:] = data
        self._update_texture(scene)
        self.denoiser_result_cached = True

    def reset_denoiser(self):
        """ Denoiser was not started yet or the user has triggered an update """
        self.denoiser_result_cached = False

        if self._denoiser_process:
            print("Interrupting denoiser")
            self._denoiser_process.terminate()
            self._denoiser_process.communicate()
            self._denoiser_process = None

    def update(self, luxcore_session, scene):
        luxcore_session.GetFilm().GetOutputFloat(self._output_type, self.buffer)
        self._update_texture(scene)

    def draw(self, engine, context, scene):
        if self._transparent:
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ONE_MINUS_SRC_ALPHA)

        engine.bind_display_space_shader(scene)

        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.texture_id)
        bgl.glBindVertexArray(self.vertex_array[0])
        bgl.glDrawArrays(bgl.GL_TRIANGLE_FAN, 0, 4)
        bgl.glBindVertexArray(NULL)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, NULL)

        engine.unbind_display_space_shader()

        err = bgl.glGetError()
        if err != bgl.GL_NO_ERROR:
            print("GL Error:", err)

        if self._transparent:
            bgl.glDisable(bgl.GL_BLEND)

    def _update_texture(self, scene):
        if self._transparent:
            gl_format = bgl.GL_RGBA
            internal_format = bgl.GL_RGBA32F
        else:
            gl_format = bgl.GL_RGB
            internal_format = bgl.GL_RGB32F

        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.texture_id)
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, internal_format, self._width, self._height,
                         0, gl_format, bgl.GL_FLOAT, self.buffer)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_EDGE)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_EDGE)

        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
        mag_filter = bgl.GL_NEAREST if scene.luxcore.viewport.mag_filter == "NEAREST" else bgl.GL_LINEAR
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, mag_filter)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, NULL)

    def _calc_offset(self, context, scene, border):
        region_size = context.region.width, context.region.height
        view_camera_offset = list(context.region_data.view_camera_offset)
        view_camera_zoom = context.region_data.view_camera_zoom
        zoom = 0.25 * ((math.sqrt(2) + view_camera_zoom / 50) ** 2)

        render = scene.render
        region_width, region_height = region_size
        border_min_x, border_max_x, border_min_y, border_max_y = border

        if context.region_data.view_perspective == "CAMERA" and render.use_border:
            # Offset is only needed if viewport is in camera mode and uses border rendering
            sensor_fit = scene.camera.data.sensor_fit

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

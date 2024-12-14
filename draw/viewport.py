import bgl
import gpu
from gpu_extras.batch import batch_for_shader

import math
import os
import numpy as np
import subprocess
import tempfile
from shutil import which
from os.path import dirname, join
from ..bin import pyluxcore
from .. import utils
from ..utils import pfm



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
        paths = cls._paths.pop(key, set())
        for path in paths:
            try:
                os.remove(path)

            except FileNotFoundError:
                pass



    @classmethod
    def cleanup(cls):
        for key in list(cls._paths):
            cls.delete_files(key)


class FrameBuffer(object):
    """ FrameBuffer used for viewport render """

    def __init__(self, engine, context, scene):
        filmsize = utils.calc_filmsize(scene, context)
        self._width, self._height = filmsize
        self._border = utils.calc_blender_border(scene, context)
        self._offset_x, self._offset_y = self._calc_offset(context, scene, self._border)
        self._pixel_size = int(scene.luxcore.viewport.pixel_size)

        self._transparent = self._initialize_transparency(scene, context)
        bufferdepth = 4 if self._transparent else 3
        self._buffertype = bgl.GL_RGBA if self._transparent else bgl.GL_RGB
        self._output_type = (
            pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
            if self._transparent else
            pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE
        )

        self.buffer = gpu.types.Buffer('FLOAT', [self._width * self._height * bufferdepth])
        self._init_opengl()


        # Denoiser initialization
        self._initialize_denoiser_paths()
        self._denoiser_process = None
        self.denoiser_result_cached = False

    def _initialize_transparency(self, scene, context):
        if utils.is_valid_camera(scene.camera) and not utils.in_material_shading_mode(context):
            return scene.camera.data.luxcore.imagepipeline.transparent_film
        return False

    def _initialize_denoiser_paths(self):
        base_path = tempfile.gettempdir()
        unique_id = id(self)
        self._noisy_file_path = join(base_path, f"{unique_id}_noisy.pfm")
        self._albedo_file_path = join(base_path, f"{unique_id}_albedo.pfm")
        self._normal_file_path = join(base_path, f"{unique_id}_normal.pfm")
        self._denoised_file_path = join(base_path, f"{unique_id}_denoised.pfm")

        current_dir = dirname(os.path.realpath(__file__))
        addon_dir = dirname(current_dir)
        self._denoiser_path = which(
            "oidnDenoise",
            path=os.pathsep.join([join(addon_dir, "bin"), os.environ["PATH"]])
        )

    def _init_opengl(self):
        width, height = self._width * self._pixel_size, self._height * self._pixel_size
        x, y = self._offset_x, self._offset_y

        position = [
            (x, y), (x + width, y), (x + width, y + height),
            (x, y + height), (x, y), (x + width, y + height)
        ]

        self.shader = gpu.shader.from_builtin('IMAGE')
        self.batch = batch_for_shader(
            self.shader, 'TRIS',
            {"pos": position, "texCoord": [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0), (1, 1)]}

        # Denoiser
        self._noisy_file_path = self._make_denoiser_filepath("noisy")
        self._albedo_file_path = self._make_denoiser_filepath("albedo")
        self._normal_file_path = self._make_denoiser_filepath("normal")
        self._denoised_file_path = self._make_denoiser_filepath("denoised")
        current_dir = dirname(os.path.realpath(__file__))
        addon_dir = dirname(current_dir)  # Go up one level
        self._denoiser_path = which("oidnDenoise",
                                    path=os.path.join(addon_dir, "bin") + os.pathsep + os.environ["PATH"])
        self._denoiser_process = None
        self.denoiser_result_cached = False

    def _init_opengl(self):
        width = self._width * self._pixel_size
        height = self._height * self._pixel_size

        position = (
            (self._offset_x, self._offset_y),
            (self._offset_x + width, self._offset_y),
            (self._offset_x + width, self._offset_y + height),
            (self._offset_x, self._offset_y + height)
        )

        self.shader = gpu.shader.from_builtin('2D_IMAGE')
        self.batch = batch_for_shader(
            self.shader, 'TRI_FAN',
            {
                "pos": position,
                "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
            },

        )

    def __del__(self):
        del self.buffer

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

    def _calc_offset(self, context, scene, border):
        region_size = context.region.width, context.region.height
        view_camera_offset = list(context.region_data.view_camera_offset)
        view_camera_zoom = context.region_data.view_camera_zoom
        zoom = 0.25 * ((math.sqrt(2) + view_camera_zoom / 50) ** 2)

        render = scene.render
        region_width, region_height = region_size
        border_min_x, border_max_x, border_min_y, border_max_y = border

        if context.region_data.view_perspective == "CAMERA" and render.use_border:
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

        return int(offset_x), int(offset_y)

    def _cam_border_offset(self, aspect, base, border_min, region_width, view_camera_offset, zoom):
        return (0.5 - 2 * zoom * view_camera_offset) * region_width + aspect * base * (2 * border_min - 1)

    def _make_denoiser_filepath(self, name):
        return os.path.join(tempfile.gettempdir(), str(id(self)) + "_" + name + ".pfm")

    def _save_denoiser_AOV(self, luxcore_session, film_output_type, path):

        np_buffer = np.zeros((self._height, self._width, 3), dtype="float32")

        # Bufferdepth always 3 because denoiser can't handle alpha anyway (maybe copy over alpha channel in the future)
        np_buffer = numpy.zeros((self._height, self._width, 3), dtype="float32")

        luxcore_session.GetFilm().GetOutputFloat(film_output_type, np_buffer)
        TempfileManager.track(id(self), path)
        with open(path, "w+b") as f:
            utils.pfm.save_pfm(f, np_buffer)

    def start_denoiser(self, luxcore_session):
        if not os.path.exists(self._denoiser_path):

            raise Exception("Binary not found. Download it from https://github.com/OpenImageDenoise/oidn/releases")


            raise Exception("Binary not found. Download it from "
                            "https://github.com/OpenImageDenoise/oidn/releases")

        if self._transparent:
            self._alpha = np.zeros((self._height, self._width, 1), dtype="float32")
            luxcore_session.GetFilm().GetOutputFloat(pyluxcore.FilmOutputType.ALPHA, self._alpha)

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
        shape = (self._height * self._width * 3)
        try:
            with open(self._denoised_file_path, "rb") as f:
                data, scale = utils.pfm.load_pfm(f)
            TempfileManager.delete_files(id(self))
        except FileNotFoundError:
            TempfileManager.delete_files(id(self))
            raise Exception("Denoising failed, check console for details")

        if self._transparent:
            shape = (self._height * self._width * 4)

            data = np.concatenate((data, self._alpha), axis=2)

            data = numpy.concatenate((data,self._alpha), axis=2)


        data = np.resize(data, shape)
        self.buffer[:] = data
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

    def draw(self, engine, context, scene):
        if self._transparent:
            format = 'RGBA16F'
        else:
            format = 'RGB16F'

        image = gpu.types.GPUTexture(size=(self._width, self._height), layers=0, is_cubemap=False, format=format,
                                     data=self.buffer)
        self.shader.uniform_sampler("image", image)
        self.batch.draw(self.shader)



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


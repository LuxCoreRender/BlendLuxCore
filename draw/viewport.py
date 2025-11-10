_needs_reload = "bpy" in locals()

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

import math
import threading
import os
import numpy as np
import tempfile
from shutil import which
from os.path import dirname
import pyluxcore
from .. import utils
from ..utils import pfm

if _needs_reload:
    import importlib

    importlib.reload(pyluxcore)
    importlib.reload(utils)


def run_denoiser(framebuffer, engine):
    """Denoiser worker."""
    session = engine.session
    film = session.GetFilm()
    film.ApplyOIDN(0)  # Apply on first stage in pipeline

    framebuffer.update(session, execute_imagepipeline=False)
    framebuffer.draw()
    framebuffer.denoised = True
    engine.tag_redraw()


class FrameBuffer:
    """FrameBuffer used for viewport render"""

    def __init__(self, engine, context, scene):
        filmsize = utils.calc_filmsize(scene, context)
        self._width, self._height = filmsize
        self._border = utils.calc_blender_border(scene, context)
        self._offset_x, self._offset_y = self._calc_offset(
            context, scene, self._border
        )
        self._pixel_size = int(scene.luxcore.viewport.pixel_size)

        self._transparent = self._initialize_transparency(scene, context)
        bufferdepth = 4 if self._transparent else 3
        self._output_type = (
            pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
            if self._transparent
            else pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE
        )

        self.buffer = gpu.types.Buffer(
            "FLOAT", [self._width * self._height * bufferdepth]
        )
        self._init_opengl()

        # Denoiser
        self.denoised = False  # Set to true after denoising
        self._denoiser_thread = None

    def _initialize_transparency(self, scene, context):
        if utils.is_valid_camera(
            scene.camera
        ) and not utils.in_material_shading_mode(context):
            return scene.camera.data.luxcore.imagepipeline.transparent_film
        return False

    def _init_opengl(self):
        width, height = (
            self._width * self._pixel_size,
            self._height * self._pixel_size,
        )
        x, y = self._offset_x, self._offset_y

        position = [
            (x, y),
            (x + width, y),
            (x + width, y + height),
            (x, y + height),
            (x, y),
            (x + width, y + height),
        ]

        self.shader = gpu.shader.from_builtin("IMAGE")
        self.batch = batch_for_shader(
            self.shader,
            "TRIS",
            {
                "pos": position,
                "texCoord": [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0), (1, 1)],
            },
        )

    def __del__(self):
        del self.buffer

    def needs_replacement(self, context, scene):
        if (self._width, self._height) != utils.calc_filmsize(scene, context):
            return True
        valid_cam = utils.is_valid_camera(scene.camera)
        if valid_cam:
            if (
                self._transparent
                != scene.camera.data.luxcore.imagepipeline.transparent_film
            ):
                return True
        elif self._transparent:
            # By default (if no camera is available), the film is not transparent
            return True
        new_border = utils.calc_blender_border(scene, context)
        if self._border != new_border:
            return True
        if (self._offset_x, self._offset_y) != self._calc_offset(
            context, scene, new_border
        ):
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

        if (
            context.region_data.view_perspective == "CAMERA"
            and render.use_border
        ):
            # Offset is only needed if viewport is in camera mode and uses
            # border rendering
            sensor_fit = scene.camera.data.sensor_fit

            aspectratio, aspect_x, aspect_y = utils.calc_aspect(
                render.resolution_x * render.pixel_aspect_x,
                render.resolution_y * render.pixel_aspect_y,
                sensor_fit,
            )

            base = 0.5 * zoom
            if sensor_fit == "AUTO":
                base *= max(region_width, region_height)
            elif sensor_fit == "HORIZONTAL":
                base *= region_width
            elif sensor_fit == "VERTICAL":
                base *= region_height

            offset_x = self._cam_border_offset(
                aspect_x,
                base,
                border_min_x,
                region_width,
                view_camera_offset[0],
                zoom,
            )
            offset_y = self._cam_border_offset(
                aspect_y,
                base,
                border_min_y,
                region_height,
                view_camera_offset[1],
                zoom,
            )

        else:
            offset_x = region_width * border_min_x + 1
            offset_y = region_height * border_min_y + 1

        # offset_x, offset_y are in pixels
        return int(offset_x), int(offset_y)

    def _cam_border_offset(
        self, aspect, base, border_min, region_width, view_camera_offset, zoom
    ):
        return (
            0.5 - 2 * zoom * view_camera_offset
        ) * region_width + aspect * base * (2 * border_min - 1)

    def start_denoiser(self, engine):
        self._denoiser_thread = threading.Thread(
            target=run_denoiser,
            args=(self, engine),
        )
        self._denoiser_thread.run()

    def is_denoiser_active(self):
        return self._denoiser_thread and self._denoiser_thread.is_alive()

    def reset_denoiser(self):
        self.denoiser_result_cached = False  # TODO
        print("RESET DENOISER")
        self.denoised = False
        if self._denoiser_thread is None:
            return
        self._denoiser_thread = None

    def update(self, luxcore_session, execute_imagepipeline=True):
        # The gpu buffer uses 16-bit float. Values >= 65520 get cast to
        # infinty, leading to a black viewport.
        # Here, I need to get the data into a separate numpy array to handle
        # the clamping.
        bufferdepth = 4 if self._transparent else 3
        size = self._width * self._height * bufferdepth
        data = np.empty(size, dtype=np.float32)
        luxcore_session.GetFilm().GetOutputFloat(
            self._output_type,
            data,
            0,  # index
            execute_imagepipeline
        )
        data[data > 65519] = 65519
        self.buffer = gpu.types.Buffer(
            "FLOAT", [self._width * self._height * bufferdepth], data
        )

    def draw(self):
        format = "RGBA16F" if self._transparent else "RGB16F"
        image = gpu.types.GPUTexture(
            size=(self._width, self._height),
            layers=0,
            is_cubemap=False,
            format=format,
            data=self.buffer,
        )
        self.shader.uniform_sampler("image", image)
        self.batch.draw(self.shader)

# Copyright (C) 2025 AUTHORS

# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, version 3.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

"""Utilities for draw."""

import numpy as np
import bpy
import pyluxcore


class ConvertFilmChannelOutput:
    """Inject a LuxCore film output into a Blender rendering buffer."""

    def __init__(
        self,
        src_depth: int,
        src_dtype: np.dtype,
        dst_depth: int,
        *,
        normalize: bool = False,
        is_id: bool = False,  # Only for src_dtype == np.uint32
    ):
        self.src_depth = int(src_depth)
        self.dst_depth = int(dst_depth)
        self.src_dtype = np.dtype(src_dtype)
        self.normalize = bool(normalize)
        self.is_id = bool(is_id)

        # Various checks
        if self.src_depth not in [1, 2, 3, 4]:
            raise ValueError(
                f"AOV: Bad value for source depth: '{self.src_depth}'"
            )
        if self.src_dtype not in [np.uint32, np.float32]:
            raise ValueError(
                f"AOV: Bad value for source dtype: '{self.src_dtype}'"
            )

    @staticmethod
    def check_size(render_engine, width, height):
        """Check consistency between LuxCore and Blender buffer sizes."""
        resx, resy = render_engine.resolutionx, render_engine.resolutiony

        if resx != width or resy != height:
            msg = (
                f"Size mismatch: Blender buffer size: {resx}x{resy} "
                f"versus LuxCore size: {width}x{height}"
            )
            raise ValueError(msg)

    def __call__(
        self,
        film: pyluxcore.Film,
        output_type: pyluxcore.FilmOutputType,
        output_index: int,
        width: int,
        height: int,
        render_pass: bpy.types.RenderPass,
        execute_image_pipeline: bool,
    ):
        # Destination depth - in most cases, it is 4; but for UV, it will be 3
        dst_depth = self.dst_depth

        # Get LuxCore data in a float buffer
        buf = np.empty([width, height, self.src_depth], dtype=self.src_dtype)
        if self.src_dtype == np.float32:
            film.GetOutputFloat(
                output_type, buf, output_index, execute_image_pipeline
            )
        elif self.src_dtype == np.uint32:
            film.GetOutputUInt(
                output_type, buf, output_index, execute_image_pipeline
            )
            # Convert buffer to float
            buf = buf.astype(np.float32)

        else:
            raise ValueError(
                "ConvertFilmChannelOutput: "
                f"Unhandled source type ('{self.src_dtype}'"
            )

        # Reshape source buffer
        if self.src_depth == 1 and self.dst_depth == 4 and self.src_dtype == np.float32:
            # Repeat on RGB and pad with 1.f in alpha channel
            buf = np.concat(
                (buf.repeat(3, axis=-1), np.ones(shape=buf.shape)), axis=2
            )
        elif self.src_depth == 1 and self.dst_depth == 1 and self.src_dtype == np.uint32:
            if self.is_id:
                buf /= 2**32

        elif self.src_depth == 2 and self.dst_depth == 3:
            # This is for UV channel
            # We need to pad the UV pass to 3 elements (Blender can't handle 2
            # elements). The third channel is a mask that is 1 where a UV map
            # exists and 0 otherwise.
            pad = ((buf[..., 0] != 0) & (buf[..., 1] != 0)).astype(np.float32)
            pad = pad.reshape(width, height, 1)
            buf = np.concat((buf, pad), axis=2)
            dst_depth = 3
        elif self.src_depth == 3 and self.dst_depth == 4:
            # Pad with 1.f in alpha channel
            buf = np.concat((buf, np.ones(shape=buf.shape)), axis=2)
        elif self.src_depth == self.dst_depth and self.src_dtype == np.float32:
            pass
        else:
            raise ValueError(
                f"AOV - Inconsistent depths: {self.src_depth} / {self.dst_depth}"
            )

        # Normalize if required.
        if self.normalize:
            # We only normalize channels 0 to 2, as channel 3 is intended for alpha
            hi_channel = min(self.src_depth, 2)
            buf_view = buf[..., 0:hi_channel]  # Basic slicing, this is a view
            assert buf_view.base is not None
            if max_value := np.max(buf_view):
                buf_view /= max_value

        # Inject into Blender buffer
        outbuf = np.reshape(buf, (-1, dst_depth)).astype(np.float32)
        render_pass.rect = outbuf.tolist()

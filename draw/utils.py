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
        *,
        normalize: bool = False,
        dst_depth: int = None,
        dst_dtype: np.dtype = np.float32,
    ):
        self.src_depth = int(src_depth)
        self.src_dtype = np.dtype(src_dtype)
        self.normalize = bool(normalize)
        self.dst_depth = int(dst_depth if dst_depth is not None else src_depth)
        self.dst_dtype = np.dtype(dst_dtype)

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
        # Get LuxCore data in a buffer
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

        # Prepare source buffer
        # Only certain combinations are allowed
        print(self.src_depth, self.dst_depth)
        if self.src_depth == self.dst_depth and self.dst_depth in (1, 2, 3, 4):
            # Same shape source/depth: nothing to do
            pass
        elif self.src_depth == 1 and self.dst_depth == 4:
            # Pad with 1.f in alpha channel
            buf = np.concat(
                (buf.repeat(3, axis=-1), np.ones(shape=buf.shape)), axis=2
            )
        elif self.src_depth == 3 and self.dst_depth == 4:
            # Pad with 1.f in alpha channel
            buf = np.concat((buf, np.ones(shape=buf.shape)), axis=2)
        elif self.src_depth == 2 and self.dst_depth == 3:
            # This is for UV channel
            # We need to pad the UV pass to 3 elements (Blender can't handle 2
            # elements). The third channel is a mask that is 1 where a UV map
            # exists and 0 otherwise.
            pad = ((buf[..., 0] != 0) & (buf[..., 1] != 0)).astype(buf.dtype)
            pad = pad.reshape(width, height, 1)
            print(pad.shape, buf.shape)
            buf = np.concat((buf, pad), axis=2)
            print(buf)
        else:
            raise ValueError(
                "ConvertFilmChannelOutput: inconsistent source and "
                f"destination depths: {self.src_depth} vs {self.dst_depth}"
            )

        # Normalize if required.
        # We only normalize channel 0 to 2, as channel 3 is intended for alpha
        if self.normalize:
            hi_channel = min(self.src_depth, 2)
            buf_view = buf[..., 0:hi_channel]  # Basic slicing, this is a view
            assert buf_view.base is not None
            if (max_value := np.max(buf_view)):
                buf_view /= max_value

        # Inject into Blender buffer
        outbuf = np.reshape(buf, (-1, self.dst_depth)).astype(self.dst_dtype)
        print(outbuf)
        render_pass.rect = outbuf.tolist()

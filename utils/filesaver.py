import bpy
import os
from . import get_abspath, get_current_render_layer


def get_output_path(scene, frame):
    config = scene.luxcore.config

    filesaver_path = config.filesaver_path
    output_path = get_abspath(filesaver_path, must_exist=True, must_be_existing_dir=True)

    blend_name = bpy.path.basename(bpy.data.filepath)
    blend_name = os.path.splitext(blend_name)[0]  # remove ".blend"

    if not blend_name:
        blend_name = "Untitled"

    dir_name = blend_name + "_LuxCore"
    frame_name = "%05d" % frame

    # If we have multiple render layers, we append the layer name
    if len(scene.render.layers) > 1:
        render_layer = get_current_render_layer(scene)
        frame_name += "_" + render_layer.name

    if config.filesaver_format == "BIN":
        # For binary format, the frame number is used as file name instead of directory name
        frame_name += ".bcf"
        output_path = os.path.join(output_path, dir_name)
    else:
        # For text format, we use the frame number as name for a subfolder
        output_path = os.path.join(output_path, dir_name, frame_name)

    return output_path, frame_name
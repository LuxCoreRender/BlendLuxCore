import os
from random import randint
import bpy
from bpy.props import CollectionProperty, StringProperty, BoolProperty
from bpy.types import OperatorFileListElement
from bpy_extras.io_utils import ImportHelper
from bpy_extras.image_utils import load_image
from mathutils import Vector

from ..nodes import TREE_TYPES

# Blender images always include an alpha channel
IMAGE_CHANNEL_COUNT = 4


def get_normal(pixels, index):
    # The index is in pixels
    index *= IMAGE_CHANNEL_COUNT
    # +3 because we don't want the alpha channel
    # Note: this call is super slow
    raw = pixels[index:index + 3]
    # The vector values (range -1..1) are encoded
    # in range 0..1, we have to map them back
    return Vector((value * 2 - 1 for value in raw))


def check_for_normalmap_slow(image):
    """
    Check the vector length of a few pixels in the image.
    If all vectors seem to be normalized, it is most likely a normalmap.
    Note: this function is super slow (because of calls to
    image.size and image.pixels)
    """
    TEST_PIXEL_COUNT = 20
    MAX_DEVIATION = 0.1
    ALLOWED_MIN = 1 - MAX_DEVIATION
    ALLOWED_MAX = 1 + MAX_DEVIATION
    # Just assume that the image is at least 100x100
    pixel_count = image.size[0] * image.size[1]

    for i in range(TEST_PIXEL_COUNT):
        index = randint(0, pixel_count - 1)
        normal = get_normal(image.pixels, index)
        length = normal.length_squared
        if length < ALLOWED_MIN or length > ALLOWED_MAX:
            return False
    return True


class LUXCORE_OT_import_multiple_images(bpy.types.Operator, ImportHelper):
    """"""
    bl_idname = "luxcore.import_multiple_images"
    bl_label = "Import Multiple Images"
    bl_description = "Import multiple imagemaps into the node editor at once"
    bl_options = {"UNDO"}

    detect_normalmaps_fast: BoolProperty(name="Auto-Detect Normalmaps (fast)", default=True,
                                          description='Check if the filename contains the string "normal"')
    detect_normalmaps_slow: BoolProperty(name="Auto-Detect Normalmaps (slow)", default=False,
                                          description="Check if the image pixels are normalized vectors "
                                                      "(takes about half a second per 4k image)")
    files: CollectionProperty(name="File Path", type=OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')
    filter_glob: StringProperty(
        default="*.jpg;*.jpeg;*.png;*.gif;*.tga;*.tif;*.tiff;*.exr;*.hdr",
        options={'HIDDEN'}
    )
    filename_ext = ""  # required by ImportHelper

    @classmethod
    def poll(cls, context):
        return (context.scene.render.engine == "LUXCORE"
                and getattr(context.space_data, "node_tree", None)
                and context.space_data.node_tree.bl_idname in TREE_TYPES)

    def execute(self, context):
        location = context.space_data.cursor_location

        for file_elem in self.files:
            print("Importing image:", file_elem.name)
            filepath = os.path.join(self.directory, file_elem.name)

            image = load_image(filepath, check_existing=True)

            node_tree = context.space_data.node_tree
            node = node_tree.nodes.new('LuxCoreNodeTexImagemap')
            node.image = image
            node.location = location
            # Nodes are spawned in a vertical column
            location.y -= 400

            if image:
                if self.detect_normalmaps_fast and "normal" in image.name:
                    node.is_normal_map = True
                elif self.detect_normalmaps_slow and check_for_normalmap_slow(image):
                    node.is_normal_map = True
            else:
                self.report({"ERROR"}, "Failed: " + file_elem.name)
                print("ERROR: Could not import", filepath)

        return {'FINISHED'}
import os
import bpy
from bpy.props import CollectionProperty, StringProperty
from bpy.types import OperatorFileListElement
from bpy_extras.io_utils import ImportHelper
from bpy_extras.image_utils import load_image

from ..nodes import TREE_TYPES


class LUXCORE_OT_import_multiple_images(bpy.types.Operator, ImportHelper):
    """"""
    bl_idname = "luxcore.import_multiple_images"
    bl_label = "Import Multiple Images"
    bl_description = "Import multiple imagemaps into the node editor at once"

    files = CollectionProperty(name="File Path", type=OperatorFileListElement)
    directory = StringProperty(subtype='DIR_PATH')
    filter_glob = StringProperty(
        default="*.jpg;*.jpeg;*.png;*.gif;*.tga;*.tif;*.tiff;*.exr;*.hdr",
        options={'HIDDEN'}
    )
    filename_ext = ""  # required by ImportHelper

    @classmethod
    def poll(cls, context):
        return (context.scene.render.engine == "LUXCORE"
                and hasattr(context.space_data, "node_tree")
                and context.space_data.node_tree.bl_idname in TREE_TYPES)

    def execute(self, context):
        location = context.space_data.cursor_location

        for file_elem in self.files:
            print("Importing image:", file_elem.name)
            filepath = os.path.join(self.directory, file_elem.name)

            image = load_image(filepath, check_existing=True)

            if image is None:
                self.report({"ERROR"}, "Failed: " + file_elem.name)
                print("Could not import", filepath)

            node_tree = context.space_data.node_tree
            node = node_tree.nodes.new('LuxCoreNodeTexImagemap')
            node.image = image
            node.location = location
            # Nodes are spawned in a vertical column
            location.y -= 400

        return {'FINISHED'}
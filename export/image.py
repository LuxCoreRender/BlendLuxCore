import bpy
import tempfile
import os
from .. import utils


class ImageExporter(object):
    """
    This class is a singleton
    """
    temp_images = {}

    @classmethod
    def _save_to_temp_file(cls, image):
        key = utils.make_key(image)

        if key in cls.temp_images:
            # Image was already exported
            temp_image = cls.temp_images[key]
        else:
            temp_image = tempfile.NamedTemporaryFile(delete=False)
            cls.temp_images[key] = temp_image

            # Save image to disk (we temporarily need a fresh scene because if we don't
            # specify it, Blender applies the current scene's exposure settings etc.
            # to the saved image (we don't want this))
            tmp_scene = bpy.data.scenes.new("__LUXCORE_IMAGE_EXPORT__")
            image.save_render(temp_image.name, tmp_scene)
            bpy.data.scenes.remove(tmp_scene)

            print("Created temp image:", temp_image.name)

        return temp_image.name

    @classmethod
    def export(cls, image):
        if image.source == "GENERATED":
            return cls._save_to_temp_file(image)
        elif image.source == "FILE":
            if image.packed_file:
                return cls._save_to_temp_file(image)
            else:
                return bpy.path.abspath(image.filepath, library=image.library)
        elif image.source == "SEQUENCE":
            # TODO
            raise NotImplementedError("Sequence not supported yet")
        else:
            raise Exception('Unsupported image source "%s" in image "%s"' % (image.source, image.name))

    @classmethod
    def cleanup(cls):
        for temp_image in cls.temp_images.values():
            print("Deleting temporary image:", temp_image.name)
            os.remove(temp_image.name)

        cls.temp_images = {}


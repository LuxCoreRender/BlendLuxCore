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
    def _save_to_temp_file(cls, image, scene):
        key = utils.make_key(image)

        if key in cls.temp_images:
            # Image was already exported
            temp_image = cls.temp_images[key]
        else:
            _, extension = os.path.splitext(image.filepath_raw)
            temp_image = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
            cls.temp_images[key] = temp_image

            print('Unpacking image "%s" to temp file "%s"' % (image.name, temp_image.name))
            orig_filepath = image.filepath_raw
            image.filepath_raw = temp_image.name
            image.save()
            image.filepath_raw = orig_filepath

        return temp_image.name

    @classmethod
    def export(cls, image, scene=None):
        if image.source == "GENERATED":
            return cls._save_to_temp_file(image, scene)
        elif image.source == "FILE":
            if image.packed_file:
                return cls._save_to_temp_file(image, scene)
            else:
                filepath = utils.get_abspath(image.filepath, library=image.library, must_exist=True, must_be_file=True)
                if filepath:
                    return filepath
                else:
                    raise OSError('Could not find image "%s" at path "%s"' % (image.name, image.filepath))
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


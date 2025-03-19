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
        # Note: We can't use utils.make_key(image) here because the memory address
        # might be re-used on undo, causing a key collision
        if image.filepath_raw:
            key = image.filepath_raw
        else:
            key = image.name

        if key in cls.temp_images:
            # Image was already exported
            temp_image = cls.temp_images[key]
        else:
            if image.filepath_raw:
                _, extension = os.path.splitext(image.filepath_raw)
            else:
                # Generated images do not have a filepath, fallback to file_format
                extension = "." + image.file_format.lower()

            temp_image = tempfile.NamedTemporaryFile(delete=False, suffix=extension)

            print('Unpacking image "%s" to temp file "%s"' % (image.name, temp_image.name))
            orig_filepath = image.filepath_raw
            orig_source = image.source
            image.filepath_raw = temp_image.name

            try:
                image.save()
            except RuntimeError as error:
                raise OSError(str(error))
            finally:
                # The changes above altered the source to "FILE", so we have to restore the original source
                image.filepath_raw = orig_filepath
                image.source = orig_source

            # Only store the key once we are sure that everything went OK
            cls.temp_images[key] = temp_image
        return temp_image.name

    @classmethod
    def export(cls, image, image_user, scene):
        if image.source == "GENERATED":
            return cls._save_to_temp_file(image)
        elif image.source == "FILE":
            if image.packed_file:
                return cls._save_to_temp_file(image)
            else:
                try:
                    filepath = utils.get_abspath(image.filepath, library=image.library,
                                                 must_exist=True, must_be_existing_file=True)
                    return filepath
                except OSError as error:
                    # Make the error message more precise
                    raise OSError('Could not find image "%s" at path "%s" (%s)'
                                  % (image.name, image.filepath, error))
        elif image.source == "SEQUENCE":
            # Note: image sequences can never be packed
            try:
                frame = image_user.get_frame(scene)
            except ValueError as error:
                raise OSError(str(error))

            indexed_filepaths = utils.image_sequence_resolve_all(image)
            try:
                if frame < 1:
                    raise IndexError
                index, filepath = indexed_filepaths[frame - 1]
                return filepath
            except IndexError:
                raise OSError('Frame %d in image sequence "%s" does not exist (contains only %d frames)'
                              % (frame, image.name, len(indexed_filepaths)))
        else:
            raise Exception('Unsupported image source "%s" in image "%s"' % (image.source, image.name))

    @classmethod
    def export_cycles_node_reader(cls, image):
        # TODO deduplicate code, support image sequences
        if image.source == "GENERATED":
            return cls._save_to_temp_file(image)
        elif image.source == "FILE":
            if image.packed_file:
                return cls._save_to_temp_file(image)
            else:
                try:
                    filepath = utils.get_abspath(image.filepath, library=image.library,
                                                 must_exist=True, must_be_existing_file=True)
                    return filepath
                except OSError as error:
                    # Make the error message more precise
                    raise OSError('Could not find image "%s" at path "%s" (%s)'
                                  % (image.name, image.filepath, error))
        else:
            raise Exception('Unsupported image source "%s" in image "%s"' % (image.source, image.name))

    @classmethod
    def cleanup(cls):
        for temp_image in cls.temp_images.values():
            filepath = temp_image.name
            temp_image.close()
            print("Deleting temporary image:", filepath)
            os.remove(filepath)

        cls.temp_images.clear()


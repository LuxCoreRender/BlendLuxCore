"""This module provides export feature for Blender image objects"""

import tempfile
import os
from .. import utils


class ImageExporter:
    """
    This class is a singleton
    """

    temp_images = {}

    @classmethod
    def _save_to_temp_file(cls, image):
        """Save packed files from an image.

        Nota bene:
        - The input image is supposed to contain exactly ONE packed file.
          This is a design limitation at this stage.
        - We don't use 'image.save', as we don't need the conversion features
          it provides and, on the other hand, we need several formats
          (including dds) that this method does not handle.
        """
        assert image.packed_file

        result = []
        for packed in image.packed_files:

            # Save original filepath
            orig_filepath = packed.filepath

            # Compute key
            # Note: We can't use utils.make_key(image) here because the memory
            # address might be re-used on undo, causing a key collision
            key = orig_filepath or f"{image.name}-{packed.tile_number}"

            # Check whether packed image has already been exported
            try:
                temp_image = cls.temp_images[key]
                print(f"[BLC] '{key}' already exported - skip")
                continue
            except KeyError:
                pass

            # Compute filename extension
            if orig_filepath:
                _, extension = os.path.splitext(orig_filepath)
            else:
                # Generated images do not have a filepath, fallback to
                # file_format
                extension = f".{image.file_format.lower()}"

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=extension
            ) as temp_image:
                packed.filepath = temp_image.name
                print(
                    f"[BLC] Unpacking image '{image.name}' to temp file "
                    f"'{temp_image.name}'"
                )

                try:
                    packed.save()
                except RuntimeError as error:
                    print("[BLC] Warning: could not save image. ", str(error))
                    continue
                finally:
                    # The changes above altered the file path, so we have to
                    # restore the original one
                    packed.filepath = orig_filepath

            # Only store the key once we are sure that everything went OK
            cls.temp_images[key] = temp_image

            result.append(temp_image.name)

        # Design limitation: the rest of BLC assumes there is only one packed
        # file per image, so we'll adapt the output.
        # If one day this limitation is removed, the code above is ready for
        # multiple packed files per image
        if (len(result)) > 1:
            print(
                f"[BLC] Warning: image '{image.name}' contains multiple "
                "packed files but only one will be used"
            )
        return result[0] if result else None

    @classmethod
    def export(cls, image, image_user, scene):
        """Export image.

        This is the main method of the module.
        """
        if image.source == "GENERATED":
            return cls._save_to_temp_file(image)

        if image.source == "FILE":
            if image.packed_file:
                return cls._save_to_temp_file(image)

            try:
                filepath = utils.get_abspath(
                    image.filepath,
                    library=image.library,
                    must_exist=True,
                    must_be_existing_file=True,
                )
                return filepath
            except OSError as error:
                # Make the error message more precise
                raise OSError(
                    f"Could not find image '{image.name}' "
                    f"at path '{image.filepath}' ({error})"
                ) from error

        if image.source == "SEQUENCE":
            # Note: image sequences can never be packed
            try:
                frame = image_user.get_frame(scene)
            except ValueError as error:
                raise RuntimeError(str(error)) from error

            indexed_filepaths = utils.image_sequence_resolve_all(image)
            try:
                if frame < 1:
                    raise IndexError
                _, filepath = indexed_filepaths[frame - 1]
                return filepath
            except IndexError as error:
                raise RuntimeError(
                    f'Frame {frame} in image sequence "{image.name}" '
                    "does not exist (contains only "
                    f'"{len(indexed_filepaths)}" frames)'
                ) from error

        # Unhandled source
        raise NotImplementedError(
            f"Unsupported image source '{image.source}' "
            f"in image '{image.name}'"
        )

    @classmethod
    def export_cycles_node_reader(cls, image):
        """Export cycles node reader."""
        # TODO deduplicate code, support image sequences
        if image.source == "GENERATED":
            return cls._save_to_temp_file(image)

        if image.source == "FILE":
            if image.packed_file:
                return cls._save_to_temp_file(image)

            try:
                filepath = utils.get_abspath(
                    image.filepath,
                    library=image.library,
                    must_exist=True,
                    must_be_existing_file=True,
                )
                return filepath
            except OSError as error:
                # Make the error message more precise
                raise OSError(
                    f'Could not find image "{image.name}" '
                    f'at path "{image.filepath}" ({error})'
                ) from error

        raise NotImplementedError(
            f'Unsupported image source "{image.source}" '
            f'in image "{image.name}"'
        )

    @classmethod
    def cleanup(cls):
        """Remove cached images."""
        for temp_image in cls.temp_images.values():
            filepath = temp_image.name
            temp_image.close()
            print("Deleting temporary image:", filepath)
            os.remove(filepath)

        cls.temp_images.clear()

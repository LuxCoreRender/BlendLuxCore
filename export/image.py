import bpy
import tempfile
import os
import threading  # Import threading for thread-safe operations
import multiprocessing  # Import multiprocessing for parallel processing
from .. import utils
import logging
import time

# Set up a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

class ImageExporter(object):
    """
    This class is a singleton for exporting images to temporary files or packing.
    """
    temp_images = {}
    _lock = threading.Lock()  # Thread-safe lock for shared resources
    _pool = None  # Placeholder for the multiprocessing pool
    
    @classmethod
    def _init_pool(cls, num_workers=None):
        """
        Initialize the multiprocessing pool.
        """
        cls._pool = multiprocessing.Pool(processes=num_workers or multiprocessing.cpu_count())
    
    @classmethod
    def _save_to_temp_file(cls, image):
        """
        Save the image to a temporary file. Avoids overwriting if already exported.
        """
        if image.filepath_raw:
            key = image.filepath_raw
        else:
            key = image.name

        try:
            with cls._lock:
                # Check if image already exists in the temp_images dictionary
                if key in cls.temp_images:
                    # Image was already exported, reuse the existing temp file
                    temp_image = cls.temp_images[key]
                else:
                    # If the image doesn't have a file path, use the file format
                    if image.filepath_raw:
                        _, extension = os.path.splitext(image.filepath_raw)
                    else:
                        extension = "." + image.file_format.lower()

                    # Create a new temporary file for the image
                    temp_image = tempfile.NamedTemporaryFile(delete=False, suffix=extension)

                    logger.debug(f'Unpacking image "{image.name}" to temp file "{temp_image.name}"')

                    # Save the image to the temp file
                    orig_filepath = image.filepath_raw
                    orig_source = image.source
                    image.filepath_raw = temp_image.name

                    image.save()

                    # Restore original image properties after saving
                    image.filepath_raw = orig_filepath
                    image.source = orig_source

                    # Store the temp file once everything went OK
                    cls.temp_images[key] = temp_image

        except OSError as e:
            logger.error(f"Failed to save image '{image.name}' to temp file. Error: {str(e)}")
            raise RuntimeError(f"Failed to save image '{image.name}' to temp file. Error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while handling image '{image.name}'. Error: {str(e)}")
            raise RuntimeError(f"Unexpected error while handling image '{image.name}'. Error: {str(e)}")

        return temp_image.name

    @classmethod
    def _export_image(cls, image, image_user, scene):
        """
        Handles the common logic for exporting images (packed or file-based).
        """
        try:
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
                        raise OSError(f'Could not find image "{image.name}" at path "{image.filepath}" ({error})')

            elif image.source == "SEQUENCE":
                return cls._handle_sequence_export(image, image_user, scene)

            else:
                raise Exception(f'Unsupported image source "{image.source}" in image "{image.name}"')

        except Exception as e:
            logger.error(f"Failed to export image '{image.name}'. Error: {str(e)}")
            raise e

    @classmethod
    def _handle_sequence_export(cls, image, image_user, scene):
        """
        Handle the export for image sequences.
        """
        try:
            frame = image_user.get_frame(scene)
            indexed_filepaths = utils.image_sequence_resolve_all(image)

            if not (1 <= frame <= len(indexed_filepaths)):
                raise IndexError(f"Frame {frame} is out of bounds for sequence '{image.name}' with {len(indexed_filepaths)} frames.")
            index, filepath = indexed_filepaths[frame - 1]
            return filepath

        except IndexError as e:
            logger.error(f"Image sequence error for '{image.name}': {str(e)}")
            raise OSError(f"Image sequence error for '{image.name}': {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error with image sequence '{image.name}': {str(e)}")
            raise OSError(f"Unexpected error with image sequence '{image.name}': {str(e)}")

    @classmethod
    def export(cls, image, image_user, scene):
        """
        Export the image based on its source (generated, packed, or file-based).
        """
        return cls._export_image(image, image_user, scene)

    @classmethod
    def export_cycles_node_reader(cls, image):
        """
        Export the image for cycles node reader based on its source.
        """
        return cls._export_image(image, None, None)

    @classmethod
    def cleanup(cls):
        """
        Clean up temporary images by deleting the temporary files.
        """
        for temp_image in cls.temp_images.values():
            filepath = temp_image.name
            temp_image.close()
            logger.debug(f"Deleting temporary image: {filepath}")
            os.remove(filepath)

        cls.temp_images.clear()

    @classmethod
    def export_images_parallel(cls, images, image_user, scene):
        """
        Export images concurrently using multiprocessing to decrease overall time.
        """
        if cls._pool is None:
            cls._init_pool()  # Initialize the pool if it wasn't created yet

        # Start multiprocessing for exporting images
        start_time = time.time()
        results = cls._pool.starmap(cls.export, [(image, image_user, scene) for image in images])
        logger.info(f"Exporting {len(images)} images took {time.time() - start_time:.2f} seconds")
        return results

    @classmethod
    def denoise_and_save_parallel(cls, images, image_user, scene):
        """
        Perform denoising and saving concurrently using multiprocessing.
        """
        if cls._pool is None:
            cls._init_pool()  # Initialize the pool if it wasn't created yet

        start_time = time.time()
        # Parallelize denoising and saving for multiple images
        results = cls._pool.starmap(cls.denoise_and_save_image, [(image, image_user, scene) for image in images])
        logger.info(f"Denoising and saving {len(images)} images took {time.time() - start_time:.2f} seconds")
        return results

    @staticmethod
    def denoise_and_save_image(image, image_user, scene):
        """
        Perform denoising and save the image in parallel.
        This is an example of how you could optimize denoising and saving operations.
        """
        # Example denoising operation
        logger.debug(f"Denoising image {image.name}")
        time.sleep(0.5)  # Simulating denoising time
        
        # Example save operation
        logger.debug(f"Saving image {image.name}")
        time.sleep(0.2)  # Simulating save time
        
        return f"Image {image.name} denoised and saved successfully."

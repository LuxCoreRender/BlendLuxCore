import bpy
import tempfile
import os
import shutil
import hashlib
from .. import utils


class NetworkTextureManager(object):
    """
    Manages texture file collection and path remapping for network rendering.
    When enabled, textures are either:
    - Copied to a 'textures' subdirectory in the export path with relative paths
    - Referenced with relative paths (if they're already in a subdirectory of export path)
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.reset()
    
    def reset(self):
        """Reset state for a new export"""
        self.enabled = False
        self.copy_textures = False
        self.use_relative_paths = False
        self.export_dir = None
        self.textures_dir = None
        self.copied_files = {}  # Maps source path -> destination relative path
        self.path_mappings = {}  # Maps absolute path -> path to use in scene file
    
    def setup(self, scene):
        """
        Configure the texture manager based on scene settings.
        Call this at the start of export.
        """
        self.reset()
        config = scene.luxcore.config
        
        if not config.use_filesaver:
            return
        
        self.copy_textures = config.filesaver_copy_textures
        self.use_relative_paths = config.filesaver_use_relative_paths
        self.enabled = self.copy_textures or self.use_relative_paths
        
        if not self.enabled:
            return
        
        # Determine the export directory (base path only, the full path with
        # blend name subdirectory will be created when first needed)
        filesaver_path = config.filesaver_path
        try:
            base_path = utils.get_abspath(filesaver_path, must_exist=True, must_be_existing_dir=True)
        except OSError:
            print("[NetworkTextureManager] Warning: Filesaver path does not exist, disabling texture management")
            self.enabled = False
            return
        
        # Add blend file name subdirectory (same logic as _convert_filesaver in config.py)
        blend_name = utils.get_blendfile_name()
        if not blend_name:
            blend_name = "Untitled"
        dir_name = blend_name + "_LuxCore"
        self.export_dir = os.path.join(base_path, dir_name)
        
        if self.copy_textures:
            self.textures_dir = os.path.join(self.export_dir, "textures")
    
    def get_unique_filename(self, source_path):
        """
        Generate a unique filename for a texture to avoid collisions.
        Uses a short hash of the original path + original filename.
        """
        basename = os.path.basename(source_path)
        name, ext = os.path.splitext(basename)
        
        # Create a short hash from the full path to ensure uniqueness
        path_hash = hashlib.md5(source_path.encode()).hexdigest()[:8]
        
        return f"{name}_{path_hash}{ext}"
    
    def process_path(self, absolute_path):
        """
        Process a texture path for network rendering.
        Returns the path to use in the scene file.
        
        If copy_textures is enabled, copies the file and returns relative path.
        If only use_relative_paths is enabled, tries to make path relative.
        """
        if not self.enabled or not absolute_path:
            return absolute_path
        
        # Check if we've already processed this path
        if absolute_path in self.path_mappings:
            return self.path_mappings[absolute_path]
        
        # Normalize the path
        absolute_path = os.path.normpath(os.path.abspath(absolute_path))
        
        if self.copy_textures:
            result_path = self._copy_and_get_relative_path(absolute_path)
        elif self.use_relative_paths:
            result_path = self._try_make_relative(absolute_path)
        else:
            result_path = absolute_path
        
        self.path_mappings[absolute_path] = result_path
        return result_path
    
    def _copy_and_get_relative_path(self, source_path):
        """Copy file to textures directory and return relative path"""
        if not os.path.exists(source_path):
            print(f"[NetworkTextureManager] Warning: Source file not found: {source_path}")
            return source_path
        
        # Ensure textures directory exists
        if not os.path.exists(self.textures_dir):
            os.makedirs(self.textures_dir, exist_ok=True)
        
        # Generate unique destination filename
        unique_name = self.get_unique_filename(source_path)
        dest_path = os.path.join(self.textures_dir, unique_name)
        
        # Copy the file if not already copied
        if source_path not in self.copied_files:
            try:
                shutil.copy2(source_path, dest_path)
                print(f"[NetworkTextureManager] Copied: {source_path} -> {dest_path}")
                self.copied_files[source_path] = dest_path
            except Exception as e:
                print(f"[NetworkTextureManager] Error copying {source_path}: {e}")
                return source_path
        
        # Return relative path from export directory
        return os.path.join("textures", unique_name)
    
    def _try_make_relative(self, absolute_path):
        """Try to make the path relative to the export directory"""
        try:
            rel_path = os.path.relpath(absolute_path, self.export_dir)
            # Only use relative path if it doesn't go up too many directories
            if not rel_path.startswith(".."):
                return rel_path
        except ValueError:
            # On Windows, relpath fails if paths are on different drives
            pass
        return absolute_path
    
    def finalize(self):
        """
        Called at the end of export to report statistics and cleanup.
        """
        if not self.enabled:
            return
        
        if self.copied_files:
            print(f"[NetworkTextureManager] Copied {len(self.copied_files)} texture files to {self.textures_dir}")
        
        if self.path_mappings:
            relative_count = sum(1 for p in self.path_mappings.values() if not os.path.isabs(p))
            print(f"[NetworkTextureManager] {relative_count} paths converted to relative")


# Global instance
network_texture_manager = NetworkTextureManager()


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
        """
        Export an image and return the filepath to use in the scene.
        If network texture management is enabled, handles copying/path remapping.
        """
        filepath = None
        
        if image.source == "GENERATED":
            filepath = cls._save_to_temp_file(image)
        elif image.source == "FILE":
            if image.packed_file:
                filepath = cls._save_to_temp_file(image)
            else:
                try:
                    filepath = utils.get_abspath(image.filepath, library=image.library,
                                                 must_exist=True, must_be_existing_file=True)
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
            except IndexError:
                raise OSError('Frame %d in image sequence "%s" does not exist (contains only %d frames)'
                              % (frame, image.name, len(indexed_filepaths)))
        else:
            raise Exception('Unsupported image source "%s" in image "%s"' % (image.source, image.name))
        
        # Process path through network texture manager if enabled
        if filepath:
            filepath = network_texture_manager.process_path(filepath)
        
        return filepath

    @classmethod
    def export_cycles_node_reader(cls, image):
        """
        Export for cycles node reader - similar to export() but without image_user.
        """
        filepath = None
        
        if image.source == "GENERATED":
            filepath = cls._save_to_temp_file(image)
        elif image.source == "FILE":
            if image.packed_file:
                filepath = cls._save_to_temp_file(image)
            else:
                try:
                    filepath = utils.get_abspath(image.filepath, library=image.library,
                                                 must_exist=True, must_be_existing_file=True)
                except OSError as error:
                    # Make the error message more precise
                    raise OSError('Could not find image "%s" at path "%s" (%s)'
                                  % (image.name, image.filepath, error))
        else:
            raise Exception('Unsupported image source "%s" in image "%s"' % (image.source, image.name))
        
        # Process path through network texture manager if enabled
        if filepath:
            filepath = network_texture_manager.process_path(filepath)
        
        return filepath

    @classmethod
    def cleanup(cls):
        for temp_image in cls.temp_images.values():
            filepath = temp_image.name
            temp_image.close()
            print("Deleting temporary image:", filepath)
            os.remove(filepath)

        cls.temp_images.clear()
        
        # Also finalize network texture manager
        network_texture_manager.finalize()


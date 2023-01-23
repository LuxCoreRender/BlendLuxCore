mport typing
import os
import bpy

from bpy.types import (
    Context,
    Panel,
)

ICON_DIR_NAME = "icons"

class IconManager:
    def __init__(self, additional_paths: typing.Optional[typing.List[str]] = None):
        import bpy.utils.previews
        self.icon_previews = bpy.utils.previews.new()
        self.additional_paths = additional_paths if additional_paths is not None else []
        self.load_all()

    def load_all(self) -> None:
        icons_dir = os.path.join(os.path.dirname(__file__), ICON_DIR_NAME)
        self.load_icons_from_directory(icons_dir)

        for path in self.additional_paths:
            self.load_icons_from_directory(os.path.join(path, ICON_DIR_NAME))

    def load_icons_from_directory(self, path: str) -> None:
        if not os.path.isdir(path):
            raise RuntimeError(f"Cannot load icons from {path}, it is not valid dir")

        for icon_filename in os.listdir(path):
            self.load_icon(icon_filename, path)

    def load_icon(self, filename: str, path: str) -> None:
        if not filename.endswith((".png")):
            return

        icon_basename, _ = os.path.splitext(filename)
        if icon_basename in self.icon_previews:
            return

        self.icon_previews.load(icon_basename, os.path.join(
            path, filename), "IMAGE")

    def get_icon(self, icon_name: str) -> bpy.types.ImagePreview:
        return self.icon_previews[icon_name]

    def get_icon_id(self, icon_name: str) -> int:
        return self.icon_previews[icon_name].icon_id


icon_manager = IconManager()

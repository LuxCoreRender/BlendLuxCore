import typing
import os
import bpy

NONE = "NONE"

# Node tree icons
NTREE_VOLUME = "MOD_FLUIDSIM"
NTREE_MATERIAL = "MATERIAL"
NTREE_TEXTURE = "TEXTURE"

MATERIAL = "MATERIAL"
NODETREE = "NODETREE"
OBJECT = "OBJECT_DATAMODE"
COMPOSITOR = "NODE_COMPOSITING"

INFO = "INFO"
WARNING = "ERROR"
ERROR = "CANCEL"

ADD = "ADD"  # + sign
REMOVE = "REMOVE"  # - sign, used to remove one element from a collection
CLEAR = "X"  # x sign, used to clear a link (e.g. the world volume)

ADD_KEYFRAME = "KEY_HLT"
REMOVE_KEYFRAME = "KEY_DEHLT"

LIGHTGROUP = "OUTLINER_OB_LIGHT"
LIGHTGROUP_ENABLED = "OUTLINER_OB_LIGHT"
LIGHTGROUP_DISABLED = "LIGHT"

URL = "URL"
DOWNLOAD = "IMPORT"
COPY_TO_CLIPBOARD = "COPYDOWN"
SHOW_NODETREE = "SCREEN_BACK"
DUPLICATE = "DUPLICATE"

REFRESH = "FILE_REFRESH"  # used in display/denoiser refresh buttons
START = "PLAY"
PAUSE = "PAUSE"
STOP = "QUIT"

CAMERA = "CAMERA_DATA"  # this should show a recognizable camera icon. Might need to be changed for 2.80.
WORLD = "WORLD"
IMAGE = "IMAGE_DATA"

EXPANDABLE_CLOSED = "TRIA_RIGHT"
EXPANDABLE_OPENED = "TRIA_DOWN"

FAKE_USER_ON = "FAKE_USER_ON"
FAKE_USER_OFF = "FAKE_USER_OFF"

GREEN_RHOMBUS = "KEYTYPE_JITTER_VEC"  # used to signal "better" in statistics comparison
RED_RHOMBUS = "KEYTYPE_EXTREME_VEC"  # used to signal "worse" in statistics comparison

ARROW_RIGHT = "FORWARD"

ICON_DIR_NAME = "../icons"

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
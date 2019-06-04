import bpy
from bpy.props import (
    BoolProperty, EnumProperty, StringProperty,
    PointerProperty, IntProperty
)


USE_IES_DESCRIPTION = "Use an IES file to control the shape of the emitted light"
IES_FILE_DESCRIPTION = "Specify path to IES file. Only portable if a relative path is used"
IES_TEXT_DESCRIPTION = (
    "Use Blender text block as IES file. Recommended if you plan to append/link this light later"
)
iesfile_type_items = [
    ("PATH", "File", IES_FILE_DESCRIPTION, 0),
    ("TEXT", "Text", IES_TEXT_DESCRIPTION, 1)
]
IES_MAP_DESCRIPTION = (
    "For rendering, the IES profile is baked into a texture. "
    "Use a higher resolution if the IES profile contains fine details"
)
FLIPZ_DESCRIPTION = "Flip the Z axis of the IES profile"


class LuxCoreIESProps(bpy.types.PropertyGroup):
    use: BoolProperty(name="Use IES File", default=False, description=USE_IES_DESCRIPTION)
    file_type: EnumProperty(name="IES File Type", items=iesfile_type_items, default="TEXT")
    file_path: StringProperty(name="IES File", subtype="FILE_PATH", description=IES_FILE_DESCRIPTION)
    file_text: PointerProperty(name="IES Text", type=bpy.types.Text, description=IES_TEXT_DESCRIPTION)
    flipz: BoolProperty(name="Flip IES Z Axis", default=False, description=FLIPZ_DESCRIPTION)
    map_width: IntProperty(name="X", default=512, min=2, soft_min=64, subtype="PIXEL",
                            description=IES_MAP_DESCRIPTION)
    map_height: IntProperty(name="Y", default=256, min=2, soft_min=64, subtype="PIXEL",
                             description=IES_MAP_DESCRIPTION)
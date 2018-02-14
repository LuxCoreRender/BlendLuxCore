import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty, PointerProperty


USE_IES_DESCRIPTION = "Use an IES file to control the shape of the emitted light"
IES_FILE_DESCRIPTION = "Specify path to IES file. Only portable if a relative path is used."
IES_TEXT_DESCRIPTION = (
    "Use Blender text block as IES file. Recommended if you plan to append/link this light later."
)
iesfile_type_items = [
    ("PATH", "File", IES_FILE_DESCRIPTION, 0),
    ("TEXT", "Text", IES_TEXT_DESCRIPTION, 1)
]


class LuxCoreIESProps(bpy.types.PropertyGroup):
    use = BoolProperty(name="Use IES File", default=False, description=USE_IES_DESCRIPTION)
    file_type = EnumProperty(name="IES File Type", items=iesfile_type_items, default="TEXT")
    file_path = StringProperty(name="IES File", subtype="FILE_PATH", description=IES_FILE_DESCRIPTION)
    file_text = PointerProperty(name="IES Text", type=bpy.types.Text, description=IES_TEXT_DESCRIPTION)
    flipz = BoolProperty(name="Flip IES Z Axis", default=False)
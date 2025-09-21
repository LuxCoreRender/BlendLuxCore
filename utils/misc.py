"""Miscellaneous utilities.

The advantage of placing objects here rather than in __init__.py is that these
objects will be available to utils submodules, even if utils is not fully
built, which avoids "ImportError: cannot import name 'xxx' from partially
initialised module "bl_ext.blc_dbg.BlendLuxCore.utils".
"""

def get_name_with_lib(datablock):
    """
    Format the name for display similar to Blender,
    with an "L" as prefix if from a library
    """
    text = datablock.name
    if datablock.library:
        # text += ' (Lib: "%s")' % datablock.library.name
        text = "L " + text
    return text


def pluralize(format_str, amount):
    formatted = format_str % amount
    if amount != 1:
        formatted += "s"
    return formatted



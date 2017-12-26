
from . import find_active_uv


def draw_uv_info(context, layout):
    """
    Call this function on nodes that use UV mapping (e.g. the Roughness class uses it
    when anisotropic roughness is enabled because it requires UV mapping).
    """
    if context.object.data:
        uv_textures = getattr(context.object.data, "uv_textures", [])
        if len(uv_textures) > 1:
            box = layout.box()
            box.label("LuxCore only supports one UV map", icon="INFO")
            active_uv = find_active_uv(context.object.data.uv_textures)
            box.label('Active: "%s"' % active_uv.name, icon="GROUP_UVS")
        elif len(uv_textures) == 0:
            layout.label("No UV map", icon="ERROR")

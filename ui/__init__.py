import bpy


ICON_VOLUMES = "MOD_FLUIDSIM"


def compatible_panels():
    panels = [
        "RENDER_PT_render",
        "RENDER_PT_output",
        "RENDER_PT_encoding",
        "RENDER_PT_dimensions",
        "RENDER_PT_stamp",

        # Data properties
        # Lamp
        "DATA_PT_context_lamp",
        # Mesh
        "DATA_PT_context_mesh",
        "DATA_PT_normals",
        "DATA_PT_texture_space",
        "DATA_PT_vertex_groups",
        "DATA_PT_shape_keys",
        "DATA_PT_uv_texture",
        "DATA_PT_vertex_colors",
        "DATA_PT_customdata",
        # Speaker
        "DATA_PT_context_speaker",
        "DATA_PT_speaker",
        "DATA_PT_distance",
        "DATA_PT_cone",
        "DATA_PT_custom_props_speaker",

        # World properties
        "WORLD_PT_context_world",
        "WORLD_PT_custom_props",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")

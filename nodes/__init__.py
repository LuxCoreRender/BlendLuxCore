from ..ui import icons

TREE_TYPES = {
    "luxcore_material_nodes",
    "luxcore_texture_nodes",
    "luxcore_volume_nodes",
}

TREE_ICONS = {
    "luxcore_material_nodes": icons.NTREE_MATERIAL,
    "luxcore_texture_nodes": icons.NTREE_TEXTURE,
    "luxcore_volume_nodes": icons.NTREE_VOLUME,
}

NOISE_BASIS_ITEMS = [
    ("blender_original", "Blender Original", ""),
    ("original_perlin", "Original Perlin", ""),
    ("improved_perlin", "Improved Perlin", ""),
    ("voronoi_f1", "Voronoi F1", ""),
    ("voronoi_f2", "Voronoi F2", ""),
    ("voronoi_f3", "Voronoi F3", ""),
    ("voronoi_f4", "Voronoi F4", ""),
    ("voronoi_f2f1", "Voronoi F2-F1", ""),
    ("voronoi_crackle", "Voronoi Crackle", ""),
    ("cell_noise", "Cell Noise", ""),
]

NOISE_TYPE_ITEMS = [
    ("soft_noise", "Soft", ""),
    ("hard_noise", "Hard", "")
]

MIN_NOISE_SIZE = 0.0001

COLORDEPTH_DESC = "Depth at which white light is turned into the absorption color"

from . import base, sockets
from bpy.utils import register_class, unregister_class

classes = (
    base.LuxCoreNodeTreePointer,
    sockets.LuxCoreSocketMaterial,
    sockets.LuxCoreSocketVolume,
    sockets.LuxCoreSocketFresnel,
    sockets.LuxCoreSocketMatEmission,
    sockets.LuxCoreSocketBump,
    sockets.LuxCoreSocketColor,
    sockets.LuxCoreSocketFloatUnbounded,
    sockets.LuxCoreSocketFloatPositive,
    sockets.LuxCoreSocketFloat0to1,
    sockets.LuxCoreSocketFloat0to2,
    sockets.LuxCoreSocketBumpHeight,
    sockets.LuxCoreSocketFloatDisneySheen,
    sockets.LuxCoreSocketVector,
    sockets.LuxCoreSocketRoughness,
    sockets.LuxCoreSocketIOR,
    sockets.LuxCoreSocketFilmThickness,
    sockets.LuxCoreSocketFilmIOR,
    sockets.LuxCoreSocketVolumeAsymmetry,
    sockets.LuxCoreSocketMapping2D,
    sockets.LuxCoreSocketMapping3D,
    sockets.LuxCoreSocketShape,
)


def register():
    from . import materials, shapes, textures, volumes
    materials.register()
    shapes.register()
    textures.register()
    volumes.register()

    for cls in classes:
        register_class(cls)

def unregister():
    from . import materials, shapes, textures, volumes
    materials.unregister()
    shapes.unregister()
    textures.unregister()
    volumes.unregister()

    for cls in classes:
        unregister_class(cls)

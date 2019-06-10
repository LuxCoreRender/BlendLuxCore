from . import mesh_converter
from .. import utils


def convert(obj, depsgraph, luxcore_scene, is_viewport_render, use_instancing):
    if obj.type == "EMPTY" or obj.data is None:
        print("empty export not implemented yet")
    elif obj.type == "MESH":
        print("converting mesh object")
        return convert_mesh_obj(obj, depsgraph, luxcore_scene, is_viewport_render, use_instancing)
    elif obj.type == "LIGHT":
        print("light export not implemented yet")


# TODO move to extra file?
def convert_mesh_obj(obj, depsgraph, luxcore_scene, is_viewport_render, use_instancing):
    mesh_definitions = mesh_converter.convert(obj, depsgraph, luxcore_scene, is_viewport_render, use_instancing)

    if not mesh_definitions:
        print("Got no mesh definitions from mesh_converter")
        return None

    prefix = "scene.objects."
    definitions = {}

    if is_viewport_render or use_instancing:
        transformation = utils.matrix_to_list(obj.matrix_world, depsgraph.scene_eval, apply_worldscale=True)
    else:
        transformation = None

    for shape_name, mat_index in mesh_definitions:
        definitions[shape_name + ".shape"] = shape_name
        definitions[shape_name + ".transformation"] = transformation
        definitions[shape_name + ".material"] = "__CLAY__"  # TODO

    return utils.create_props(prefix, definitions)

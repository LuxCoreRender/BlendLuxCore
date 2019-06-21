from . import mesh_converter
from .. import utils

MESH_OBJECTS = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
EXPORTABLE_OBJECTS = MESH_OBJECTS | {"LIGHT", "EMPTY"}


def convert(obj, luxcore_name_base, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform):
    if obj.type == "EMPTY" or obj.data is None:
        print("empty export not implemented yet")
    elif obj.type in MESH_OBJECTS:
        print("converting mesh object")
        return convert_mesh_obj(obj, luxcore_name_base, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform)
    elif obj.type == "LIGHT":
        print("light export not implemented yet")
        return ExportedLight(luxcore_name_base, transform)


class ExportedPart:
    def __init__(self, lux_obj, lux_shape, lux_mat):
        self.lux_obj = lux_obj
        self.lux_shape = lux_shape
        self.lux_mat = lux_mat

class ExportedObject:
    def __init__(self, lux_name_base, mesh_definitions, transform):
        self.lux_name_base = lux_name_base
        self.transform = transform
        self.parts = []

        for shape_name, mat_index in mesh_definitions:
            obj_name = lux_name_base + str(mat_index)
            mat_name = "__CLAY__"  # TODO
            self.parts.append(ExportedPart(obj_name, shape_name, mat_name))

    def get_props(self):
        prefix = "scene.objects."
        definitions = {}
        for part in self.parts:
            definitions[part.lux_obj + ".shape"] = part.lux_shape
            # Note, I'm not applying worldscale here, I hope we can get rid
            # of that (https://github.com/LuxCoreRender/BlendLuxCore/issues/97)
            definitions[part.lux_obj + ".transformation"] = utils.matrix_to_list(self.transform)
            definitions[part.lux_obj + ".material"] = part.lux_mat
        return utils.create_props(prefix, definitions)

class ExportedLight(ExportedObject):
    def __init__(self, lux_light_name, transform):
        super().__init__(lux_light_name, [], transform)

    def get_props(self):
        prefix = "scene.lights." + self.lux_name_base + "."
        definitions = {
            "type": "point",
            "transformation": utils.matrix_to_list(self.transform),
            "gain": [1] * 3,
        }
        return utils.create_props(prefix, definitions)


def convert_mesh_obj(obj, luxcore_name_base, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform):
    mesh_definitions = mesh_converter.convert(obj, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform)

    if not mesh_definitions:
        print("Got no mesh definitions from mesh_converter")
        return None

    if is_viewport_render or use_instancing:
        obj_transform = transform
    else:
        # Transform is applied to the mesh instead
        obj_transform = None

    return ExportedObject(luxcore_name_base, mesh_definitions, obj_transform)

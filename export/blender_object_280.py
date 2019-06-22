from . import mesh_converter
from .. import utils

MESH_OBJECTS = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
EXPORTABLE_OBJECTS = MESH_OBJECTS | {"LIGHT", "EMPTY"}


# I think this whole file is not needed, just complicates things. Move the stuff we use to object cache.
def convert(obj, luxcore_name_base, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform):
    if obj.type == "EMPTY" or obj.data is None:
        print("empty export not implemented yet")
    elif obj.type in MESH_OBJECTS:
        print("converting mesh object", obj.name_full)
        return convert_mesh_obj(obj, luxcore_name_base, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform)
    elif obj.type == "LIGHT":
        print("light export not implemented yet")
        return ExportedLight(luxcore_name_base, transform)


class ExportedPart:
    def __init__(self, lux_obj, lux_shape, lux_mat):
        self.lux_obj = lux_obj
        self.lux_shape = lux_shape
        self.lux_mat = lux_mat

class ExportedMesh:
    def __init__(self, mesh_definitions):
        self.mesh_definitions = mesh_definitions

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
            "gain": [30000000] * 3,
        }
        return utils.create_props(prefix, definitions)


# TODO remove this, has been moved to object cache
def convert_mesh_obj(obj, luxcore_name_base, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform):
    raise Exception("shouldnt use this")

    # Before converting curves, we might want to check if they actually generate a mesh, like Cycles does:
    # TODO profile this, check if it's actually a problem
    # if (b_ob.type() == BL::Object::type_CURVE) {
    #     /* Skip exporting curves without faces, overhead can be
    #      * significant if there are many for path animation. */
    #     BL::Curve b_curve(b_ob.data());
    #
    #     return (b_curve.bevel_object() || b_curve.extrude() != 0.0f || b_curve.bevel_depth() != 0.0f ||
    #             b_curve.dimensions() == BL::Curve::dimensions_2D || b_ob.modifiers.length());
    #   }

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

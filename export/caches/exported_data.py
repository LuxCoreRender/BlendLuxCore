from ... import utils


class ExportedPart:
    def __init__(self, lux_obj, lux_shape, lux_mat):
        self.lux_obj = lux_obj
        self.lux_shape = lux_shape
        self.lux_mat = lux_mat


class ExportedMesh:
    def __init__(self, mesh_definitions):
        self.mesh_definitions = mesh_definitions


class ExportedObject:
    # TODO id, camera visibility etc.
    def __init__(self, lux_name_base, mesh_definitions, mat_names, transform):
        self.lux_name_base = lux_name_base
        self.transform = transform
        self.parts = []

        for (shape_name, mat_index), mat_name in zip(mesh_definitions, mat_names):
            obj_name = lux_name_base + str(mat_index)
            self.parts.append(ExportedPart(obj_name, shape_name, mat_name))

    def get_props(self):
        prefix = "scene.objects."
        definitions = {}
        for part in self.parts:
            definitions[part.lux_obj + ".shape"] = part.lux_shape
            definitions[part.lux_obj + ".material"] = part.lux_mat
            # Note, I'm not applying worldscale here, I hope we can get rid
            # of that (https://github.com/LuxCoreRender/BlendLuxCore/issues/97)
            if self.transform:
                definitions[part.lux_obj + ".transformation"] = utils.matrix_to_list(self.transform)
        return utils.create_props(prefix, definitions)

    def delete(self, luxcore_scene):
        for part in self.parts:
            luxcore_scene.DeleteObject(part.lux_obj)


class ExportedLight(ExportedObject):
    def __init__(self, lux_light_name, transform):
        super().__init__(None, lux_light_name, [], transform)

    def get_props(self):
        # Should never happen
        raise NotImplementedError("get_props called on ExportedLight")

    def delete(self, luxcore_scene):
        luxcore_scene.DeleteLight(self.lux_name_base)

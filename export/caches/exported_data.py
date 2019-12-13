from ... import utils

class ExportedPart:
    def __init__(self, lux_obj, lux_shape, lux_mat):
        self.lux_obj = lux_obj
        self.lux_shape = lux_shape
        self.lux_mat = lux_mat


class ExportedMesh:
    def __init__(self, mesh_definitions):
        self.mesh_definitions = mesh_definitions


class ExportedData:
    def delete(self, luxcore_scene):
        raise NotImplementedError()


class ExportedObject(ExportedData):
    def __init__(self, lux_name_base, mesh_definitions, mat_names, transform, visible_to_camera, obj_id=-1):
        self.lux_name_base = lux_name_base
        self.transform = transform
        self.parts = []
        self.visible_to_camera = visible_to_camera
        self.obj_id = obj_id

        for (shape_name, mat_index), mat_name in zip(mesh_definitions, mat_names):
            obj_name = lux_name_base + str(mat_index)

            self.parts.append(ExportedPart(obj_name, shape_name, mat_name))

    def get_props(self):
        prefix = "scene.objects."
        definitions = {}

        for part in self.parts:
            definitions[part.lux_obj + ".shape"] = part.lux_shape
            definitions[part.lux_obj + ".material"] = part.lux_mat
            definitions[part.lux_obj + ".camerainvisible"] = not self.visible_to_camera
            if self.obj_id != -1:
                definitions[part.lux_obj + ".id"] = self.obj_id

            if self.transform:
                definitions[part.lux_obj + ".transformation"] = utils.matrix_to_list(self.transform)

        return utils.create_props(prefix, definitions)

    def delete(self, luxcore_scene):
        for part in self.parts:
            luxcore_scene.DeleteObject(part.lux_obj)


class ExportedLight(ExportedData):
    def __init__(self, lux_light_name):
        self.lux_light_name = lux_light_name

    def delete(self, luxcore_scene):
        luxcore_scene.DeleteLight(self.lux_light_name)

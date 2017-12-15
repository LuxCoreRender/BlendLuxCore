import mathutils
import math
from ..bin import pyluxcore
from .. import utils
from ..utils import ExportedObject, ExportedLight
from .image import ImageExporter


def convert(blender_obj, scene, context, luxcore_scene):
    try:
        assert blender_obj.type == "LAMP"
        print("converting lamp:", blender_obj.name)

        luxcore_name = utils.get_unique_luxcore_name(blender_obj)
        prefix = "scene.lights." + luxcore_name + "."
        definitions = {}
        exported_light = ExportedLight(luxcore_name)

        lamp = blender_obj.data

        matrix = blender_obj.matrix_world
        matrix_inv = matrix.inverted()
        sun_dir = [matrix_inv[2][0], matrix_inv[2][1], matrix_inv[2][2]]

        # Common light settings shared by all light types
        # Note: these variables are also passed to the area light export function
        gain = [x * lamp.luxcore.gain for x in lamp.luxcore.rgb_gain]
        samples = lamp.luxcore.samples
        importance = lamp.luxcore.importance

        definitions["gain"] = gain
        definitions["samples"] = samples
        definitions["importance"] = importance

        if lamp.type == "POINT":
            if lamp.luxcore.image or lamp.luxcore.iesfile:
                # mappoint
                definitions["type"] = "mappoint"

                if lamp.luxcore.image:
                    definitions["mapfile"] = ImageExporter.export(lamp.luxcore.image, scene)
                    definitions["gamma"] = lamp.luxcore.gamma
                if lamp.luxcore.iesfile:
                    # TODO: error if iesfile does not exist
                    definitions["iesfile"] = lamp.luxcore.iesfile
                    definitions["flipz"] = lamp.luxcore.flipz
            else:
                # point
                definitions["type"] = "point"

            definitions["efficency"] = lamp.luxcore.efficacy
            definitions["power"] = lamp.luxcore.power
            # Position is set by transformation property
            definitions["position"] = [0, 0, 0]
            transformation = utils.matrix_to_list(matrix, scene, apply_worldscale=True)
            definitions["transformation"] = transformation

        elif lamp.type == "SUN":
            distant_dir = [-sun_dir[0], -sun_dir[1], -sun_dir[2]]

            if lamp.luxcore.sun_type == "sun":
                # sun
                definitions["type"] = "sun"
                definitions["dir"] = sun_dir
                definitions["turbidity"] = lamp.luxcore.turbidity
                definitions["relsize"] = lamp.luxcore.relsize
            elif lamp.luxcore.theta < 0.05:
                # sharpdistant
                definitions["type"] = "sharpdistant"
                definitions["direction"] = distant_dir
            else:
                # distant
                definitions["type"] = "distant"
                definitions["direction"] = distant_dir
                definitions["theta"] = lamp.luxcore.theta

        elif lamp.type == "SPOT":
            coneangle = math.degrees(lamp.spot_size) / 2
            conedeltaangle = math.degrees(lamp.spot_size / 2 * lamp.spot_blend)

            if lamp.luxcore.image:
                # projection
                definitions["type"] = "projection"
                definitions["fov"] = coneangle * 2
                definitions["mapfile"] = ImageExporter.export(lamp.luxcore.image, scene)
                definitions["gamma"] = lamp.luxcore.gamma
            else:
                # spot
                definitions["type"] = "spot"
                definitions["coneangle"] = coneangle
                definitions["conedeltaangle"] = conedeltaangle

            definitions["efficency"] = lamp.luxcore.efficacy
            definitions["power"] = lamp.luxcore.power
            # Position and direction are set by transformation property
            definitions["position"] = [0, 0, 0]
            definitions["target"] = [0, 0, -1]

            spot_fix = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')
            transformation = utils.matrix_to_list(matrix * spot_fix, scene, apply_worldscale=True)
            definitions["transformation"] = transformation

        elif lamp.type == "HEMI":
            if lamp.luxcore.image:
                definitions["type"] = "infinite"
                definitions["file"] = ImageExporter.export(lamp.luxcore.image, scene)
                definitions["gamma"] = lamp.luxcore.gamma
                transformation = utils.matrix_to_list(matrix, scene, apply_worldscale=True)
                definitions["transformation"] = transformation
                definitions["sampleupperhemisphereonly"] = lamp.luxcore.sampleupperhemisphereonly
            else:
                # Fallback
                definitions["type"] = "constantinfinite"

        elif lamp.type == "AREA":
            if lamp.luxcore.is_laser:
                # laser
                definitions["type"] = "laser"
                definitions["radius"] = lamp.size / 2 * utils.get_worldscale(scene, as_scalematrix=False)

                definitions["efficency"] = lamp.luxcore.efficacy
                definitions["power"] = lamp.luxcore.power
                # Position and direction are set by transformation property
                definitions["position"] = [0, 0, 0]
                definitions["target"] = [0, 0, -1]

                spot_fix = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')
                transformation = utils.matrix_to_list(matrix * spot_fix, scene, apply_worldscale=True)
                definitions["transformation"] = transformation
            else:
                # area (mesh light)
                return _convert_area_lamp(blender_obj, scene, context, luxcore_scene, gain, samples, importance)

        else:
            # Can only happen if Blender changes its lamp types
            raise Exception("Unkown light type", lamp.type, 'in lamp "%s"' % blender_obj.name)

        props = utils.create_props(prefix, definitions)
        return props, exported_light
    except Exception as error:
        # TODO: collect exporter errors
        print("ERROR in light", blender_obj.name)
        print(error)
        import traceback
        traceback.print_exc()
        return pyluxcore.Properties(), None


def _convert_area_lamp(blender_obj, scene, context, luxcore_scene, gain, samples, importance):
    """
    An area light is a plane object with emissive material in LuxCore
    # TODO: check if we need to scale gain with area?
    """
    lamp = blender_obj.data
    luxcore_name = utils.get_unique_luxcore_name(blender_obj)
    props = pyluxcore.Properties()

    # Light emitting material
    mat_name = luxcore_name + "_AREA_LIGHT_MAT"
    mat_prefix = "scene.materials." + mat_name + "."
    mat_definitions = {
        "type": "matte",
        # Black base material to avoid any bounce light from the mesh
        "kd": [0, 0, 0],
        # Color is controlled by gain
        "emission": [1, 1, 1],
        "emission.gain": gain,
        "emission.power": lamp.luxcore.power,
        "emission.efficency": lamp.luxcore.efficacy,
        "emission.samples": samples,
        # "emission.theta": TODO,
        # Note: not "emission.importance"
        "importance": importance,
        # TODO: id, iesfile, maybe transparency (hacky)
    }
    mat_props = utils.create_props(mat_prefix, mat_definitions)
    props.Set(mat_props)

    # LuxCore object

    # Copy transformation of area lamp object
    transform_matrix = blender_obj.matrix_world.copy()
    scale_x = mathutils.Matrix.Scale(lamp.size / 2, 4, (1, 0, 0))
    if lamp.shape == "RECTANGLE":
        scale_y = mathutils.Matrix.Scale(lamp.size_y / 2, 4, (0, 1, 0))
    else:
        # basically scale_x, but for the y axis (note the last tuple argument)
        scale_y = mathutils.Matrix.Scale(lamp.size / 2, 4, (0, 1, 0))

    transform_matrix *= scale_x
    transform_matrix *= scale_y

    transform = utils.matrix_to_list(transform_matrix, scene, apply_worldscale=True)
    # Only bake the transform into the mesh for final renders (disables instancing which
    # is needed for viewport render so we can move the light object)
    shape_transform = None if context else transform

    shape_name = "Mesh-" + luxcore_name
    if not luxcore_scene.IsMeshDefined(shape_name):
        vertices = [
            (1, 1, 0),
            (1, -1, 0),
            (-1, -1, 0),
            (-1, 1, 0)
        ]
        faces = [
            (0, 1, 2),
            (2, 3, 0)
        ]
        luxcore_scene.DefineMesh(shape_name, vertices, faces, None, None, None, None, shape_transform)

    obj_prefix = "scene.objects." + luxcore_name + "."
    obj_definitions = {
        "material": mat_name,
        "shape": shape_name,
    }
    if context:
        # Use instancing for viewport render so we can interactively move the light
        obj_definitions["transformation"] = transform

    obj_props = utils.create_props(obj_prefix, obj_definitions)
    props.Set(obj_props)

    exported_obj = ExportedObject([luxcore_name])
    return props, exported_obj

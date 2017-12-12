import mathutils
import math
from ..bin import pyluxcore
from .. import utils

# TODO support all parameters for all possible light types

def convert(blender_obj, scene):
    assert blender_obj.type == "LAMP"
    print("converting lamp:", blender_obj.name)

    luxcore_name = utils.get_unique_luxcore_name(blender_obj)
    prefix = "scene.lights." + luxcore_name + "."
    definitions = {}

    lamp = blender_obj.data

    matrix = blender_obj.matrix_world
    matrix_inv = matrix.inverted()
    dir = [matrix_inv[2][0], matrix_inv[2][1], matrix_inv[2][2]]

    type = lamp.luxcore.type
    if type == "area":
        # Special case because it's really a mesh light
        definitions["type"] = "point"  # TODO

    elif type == "sun":
        definitions["type"] = "sun"
        definitions["dir"] = dir

    elif type == "sky2":
        definitions["type"] = "sky2"
        definitions["dir"] = dir

    # infinite and constantinfinite
    elif type == "infinite":
        definitions["type"] = "infinite"
        definitions["file"] = "/home/simon/Bilder/hdris/Ditch_River/Ditch-River_2k.hdr"

        transformation = utils.matrix_to_list(matrix, scene, apply_worldscale=True)
        definitions["transformation"] = transformation

    # point and mappoint
    elif type == "point":
        definitions["type"] = "point"
        # Position is set by transformationation property
        definitions["position"] = [0, 0, 0]

        transformation = utils.matrix_to_list(matrix, scene, apply_worldscale=True)
        definitions["transformation"] = transformation

    # spot and projector
    elif type == "spot":
        definitions["type"] = "spot"
        # Position is set by transformationation property
        definitions["position"] = [0, 0, 0]
        definitions["target"] = [0, 0, -1]

        spot_fix = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')
        transformation = utils.matrix_to_list(matrix * spot_fix, scene, apply_worldscale=True)
        definitions["transformation"] = transformation

    # distant and sharpdistant
    elif type == "distant":
        definitions["type"] = "distant"
        distant_dir = [-dir[0], -dir[1], -dir[2]]
        definitions["direction"] = distant_dir

    elif type == "laser":
        definitions["type"] = "laser"
        definitions["position"] = [0, 0, 0]
        definitions["target"] = [0, 0, -1]

        spot_fix = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')
        transformation = utils.matrix_to_list(matrix * spot_fix, scene, apply_worldscale=True)
        definitions["transformation"] = transformation

    else:
        raise Exception("Unkown light type:", type, 'in lamp "%s"' % blender_obj.name)

    # Common light settings
    # TODO rgb gain
    definitions["gain"] = [lamp.luxcore.gain] * 3

    return utils.create_props(prefix, definitions)

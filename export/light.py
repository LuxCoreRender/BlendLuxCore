import mathutils
import math
from ..bin import pyluxcore
from .. import utils

# TODO support all parameters for all possible light types

def convert(blender_obj, scene):
    try:
        assert blender_obj.type == "LAMP"
        print("converting lamp:", blender_obj.name)

        luxcore_name = utils.get_unique_luxcore_name(blender_obj)
        prefix = "scene.lights." + luxcore_name + "."
        definitions = {}

        lamp = blender_obj.data

        matrix = blender_obj.matrix_world
        matrix_inv = matrix.inverted()
        dir = [matrix_inv[2][0], matrix_inv[2][1], matrix_inv[2][2]]

        if lamp.type == "POINT":
            if lamp.luxcore.image or lamp.luxcore.iesfile:
                # mappoint
                definitions["type"] = "mappoint"
            else:
                # point
                definitions["type"] = "point"

                # Position is set by transformationation property
            definitions["position"] = [0, 0, 0]
            transformation = utils.matrix_to_list(matrix, scene, apply_worldscale=True)
            definitions["transformation"] = transformation

        elif lamp.type == "SUN":
            distant_dir = [-dir[0], -dir[1], -dir[2]]

            if lamp.luxcore.sun_type == "sun":
                # sun
                definitions["type"] = "sun"
                definitions["dir"] = dir
                definitions["turbidity"] = lamp.luxcore.turbidity
                definitions["relsize"] = lamp.luxcore.relsize
            elif lamp.luxcore.theta == 0:
                # sharpdistant
                definitions["type"] = "sharpdistant"
                definitions["direction"] = distant_dir
            else:
                # distant
                definitions["type"] = "distant"
                definitions["direction"] = distant_dir
                definitions["theta"] = lamp.luxcore.theta

        elif lamp.type == "SPOT":
            if lamp.luxcore.spot_type == "spot":
                if lamp.luxcore.image:
                    # projector
                    definitions["type"] = "projector"
                    # TODO image
                else:
                    # spot
                    definitions["type"] = "spot"
            else:
                # laser
                definitions["type"] = "laser"
                # TODO: radius

            # Position and direction is set by transformation property
            definitions["position"] = [0, 0, 0]
            definitions["target"] = [0, 0, -1]

            spot_fix = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')
            transformation = utils.matrix_to_list(matrix * spot_fix, scene, apply_worldscale=True)
            definitions["transformation"] = transformation

        elif lamp.type == "HEMI":
            if lamp.luxcore.image:
                definitions["type"] = "infinite"
                # TODO image file
                definitions["file"] = "/home/simon/Bilder/hdris/Ditch_River/Ditch-River_2k.hdr"
                transformation = utils.matrix_to_list(matrix, scene, apply_worldscale=True)
                definitions["transformation"] = transformation
            else:
                # Fallback
                definitions["type"] = "constantinfinite"

        elif lamp.type == "AREA":
            # TODO
            raise NotImplementedError("Area light not implemented yet")

        else:
            # Can only happen if Blender changes its lamp types
            raise Exception("Unkown light type", lamp.type, 'in lamp "%s"' % blender_obj.name)

        # Common light settings
        # TODO rgb gain
        gain = [x * lamp.luxcore.gain for x in lamp.luxcore.rgb_gain]
        definitions["gain"] = gain
        definitions["samples"] = lamp.luxcore.samples

        return utils.create_props(prefix, definitions)
    except Exception as error:
        # TODO: collect exporter errors
        print("ERROR in light", blender_obj.name)
        print(error)
        return pyluxcore.Properties()

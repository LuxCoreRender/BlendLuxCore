import mathutils
import math
from ..bin import pyluxcore
from .. import utils
from ..utils import ExportedObject, ExportedLight
from .image import ImageExporter


def convert(blender_obj, scene):
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

        if lamp.type == "POINT":
            if lamp.luxcore.image or lamp.luxcore.iesfile:
                # mappoint
                definitions["type"] = "mappoint"

                if lamp.luxcore.image:
                    definitions["emission.mapfile"] = ImageExporter.export(lamp.luxcore.image, scene)
                    definitions["emission.gamma"] = lamp.luxcore.gamma
                if lamp.luxcore.iesfile:
                    definitions["emission.iesfile"] = lamp.luxcore.iesfile
                    definitions["emission.flipz"] = lamp.luxcore.flipz
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
                luxcore_name = "test" # TODO
                # A mesh light is an object with emissive material in LuxCore
                exported_light = ExportedObject([luxcore_name])
                # TODO
                raise NotImplementedError("Area light not implemented yet")

        else:
            # Can only happen if Blender changes its lamp types
            raise Exception("Unkown light type", lamp.type, 'in lamp "%s"' % blender_obj.name)

        # Common light settings
        gain = [x * lamp.luxcore.gain for x in lamp.luxcore.rgb_gain]
        definitions["gain"] = gain
        definitions["samples"] = lamp.luxcore.samples
        definitions["importance"] = lamp.luxcore.importance

        props = utils.create_props(prefix, definitions)
        return props, exported_light
    except Exception as error:
        # TODO: collect exporter errors
        print("ERROR in light", blender_obj.name)
        print(error)
        import traceback
        traceback.print_exc()
        return pyluxcore.Properties(), None

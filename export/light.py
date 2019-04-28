import bpy
from mathutils import Matrix
import math
from ..bin import pyluxcore
from .. import utils
from ..utils import ExportedObject, ExportedLight
from .image import ImageExporter


WORLD_BACKGROUND_LIGHT_NAME = "__WORLD_BACKGROUND_LIGHT__"
MISSING_IMAGE_COLOR = [1, 0, 1]


def convert_lamp(exporter, obj, scene, context, luxcore_scene, dupli_suffix="", dupli_matrix=None):
    try:
        assert isinstance(obj, bpy.types.Object)
        assert obj.type == "LAMP"

        luxcore_name = utils.get_luxcore_name(obj, context) + dupli_suffix

        # If this light was previously defined as an area lamp, delete the area lamp mesh
        luxcore_scene.DeleteObject(_get_area_obj_name(luxcore_name))
        # If this light was previously defined as a light, delete it
        luxcore_scene.DeleteLight(luxcore_name)

        prefix = "scene.lights." + luxcore_name + "."
        definitions = {}
        exported_light = ExportedLight(luxcore_name)

        lamp = obj.data

        transform_matrix = dupli_matrix if dupli_matrix else obj.matrix_world
        sun_dir = _calc_sun_dir(obj)

        # Common light settings shared by all light types
        # Note: these variables are also passed to the area light export function
        gain, importance, lightgroup_id = _convert_common_props(exporter, scene, lamp)
        definitions["gain"] = gain
        definitions["importance"] = importance
        definitions["id"] = lightgroup_id

        if lamp.type == "POINT":
            if lamp.luxcore.image or lamp.luxcore.ies.use:
                # mappoint/mapsphere
                definitions["type"] = "mappoint" if lamp.luxcore.radius == 0 else "mapsphere"

                if lamp.luxcore.image:
                    try:
                        filepath = ImageExporter.export(lamp.luxcore.image,
                                                        lamp.luxcore.image_user,
                                                        scene)
                        definitions["mapfile"] = filepath
                        definitions["gamma"] = lamp.luxcore.gamma
                    except OSError as error:
                        msg = 'Lamp "%s": %s' % (obj.name, error)
                        scene.luxcore.errorlog.add_warning(msg, obj_name=obj.name)
                        # Fallback
                        definitions["type"] = "point" if lamp.luxcore.radius == 0 else "sphere"
                        # Signal that the image is missing
                        definitions["gain"] = [x * lamp.luxcore.gain for x in MISSING_IMAGE_COLOR]

                has_ies = False
                try:
                    has_ies = export_ies(definitions, lamp.luxcore.ies, lamp.library)
                except OSError as error:
                    msg = 'Lamp "%s": %s' % (obj.name, error)
                    scene.luxcore.errorlog.add_warning(msg, obj_name=obj.name)
                finally:
                    if not has_ies:
                        # Fallback
                        definitions["type"] = "point" if lamp.luxcore.radius == 0 else "sphere"
            else:
                # point/sphere
                definitions["type"] = "point" if lamp.luxcore.radius == 0 else "sphere"

            definitions["efficency"] = lamp.luxcore.efficacy
            definitions["power"] = lamp.luxcore.power
            # Position is set by transformation property
            definitions["position"] = [0, 0, 0]
            transformation = utils.matrix_to_list(transform_matrix, scene, apply_worldscale=True)
            definitions["transformation"] = transformation

            if lamp.luxcore.radius > 0:
                worldscale = utils.get_worldscale(scene, as_scalematrix=False)
                definitions["radius"] = lamp.luxcore.radius * worldscale

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
                try:
                    definitions["mapfile"] = ImageExporter.export(lamp.luxcore.image,
                                                                  lamp.luxcore.image_user,
                                                                  scene)
                    definitions["type"] = "projection"
                    definitions["fov"] = coneangle * 2
                    definitions["gamma"] = lamp.luxcore.gamma
                except OSError as error:
                    msg = 'Lamp "%s": %s' % (obj.name, error)
                    scene.luxcore.errorlog.add_warning(msg, obj_name=obj.name)
                    # Fallback
                    definitions["type"] = "spot"
                    # Signal that the image is missing
                    definitions["gain"] = [x * lamp.luxcore.gain for x in MISSING_IMAGE_COLOR]
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

            spot_fix = Matrix.Rotation(math.radians(-90.0), 4, "Z")
            transformation = utils.matrix_to_list(transform_matrix * spot_fix, scene, apply_worldscale=True)
            definitions["transformation"] = transformation

        elif lamp.type == "HEMI":
            if lamp.luxcore.image:
                _convert_infinite(definitions, lamp, scene, transform_matrix)
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

                spot_fix = Matrix.Rotation(math.radians(-90.0), 4, "Z")
                transformation = utils.matrix_to_list(transform_matrix * spot_fix, scene, apply_worldscale=True)
                definitions["transformation"] = transformation
            else:
                # area (mesh light)
                return _convert_area_lamp(obj, scene, context, luxcore_scene, gain,
                                          importance, luxcore_name, dupli_matrix)

        else:
            # Can only happen if Blender changes its lamp types
            raise Exception("Unkown light type", lamp.type, 'in lamp "%s"' % obj.name)

        _indirect_light_visibility(definitions, lamp)
        _visibilitymap(definitions, lamp)

        props = utils.create_props(prefix, definitions)
        return props, exported_light
    except Exception as error:
        msg = 'Light "%s": %s' % (obj.name, error)
        scene.luxcore.errorlog.add_warning(msg, obj_name=obj.name)
        import traceback
        traceback.print_exc()
        return pyluxcore.Properties(), None


def convert_world(exporter, world, scene):
    try:
        assert isinstance(world, bpy.types.World)
        luxcore_name = WORLD_BACKGROUND_LIGHT_NAME
        prefix = "scene.lights." + luxcore_name + "."
        definitions = {}

        gain, importance, lightgroup_id = _convert_common_props(exporter, scene, world)
        definitions["gain"] = gain
        definitions["importance"] = importance
        definitions["id"] = lightgroup_id

        light_type = world.luxcore.light
        if light_type == "sky2":
            definitions["type"] = "sky2"
            definitions["ground.enable"] = world.luxcore.ground_enable
            definitions["ground.color"] = list(world.luxcore.ground_color)
            definitions["groundalbedo"] = list(world.luxcore.groundalbedo)

            if world.luxcore.sun:
                definitions["dir"] = _calc_sun_dir(world.luxcore.sun)

                if world.luxcore.use_sun_gain_for_sky:
                    gain = [x * world.luxcore.sun.data.luxcore.gain for x in world.luxcore.rgb_gain]
                    definitions["gain"] = gain

            if world.luxcore.sun and world.luxcore.sun.data:
                # Use sun turbidity so the user does not have to keep two values in sync
                definitions["turbidity"] = world.luxcore.sun.data.luxcore.turbidity
            else:
                # Use world turbidity
                definitions["turbidity"] = world.luxcore.turbidity

        elif light_type == "infinite":
            if world.luxcore.image:
                transformation = Matrix.Rotation(world.luxcore.rotation, 4, "Z")
                _convert_infinite(definitions, world, scene, transformation)
            else:
                # Fallback if no image is set
                definitions["type"] = "constantinfinite"
        else:
            definitions["type"] = "constantinfinite"

        _indirect_light_visibility(definitions, world)
        _visibilitymap(definitions, world)

        props = utils.create_props(prefix, definitions)
        return props
    except Exception as error:
        msg = 'World "%s": %s' % (world.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()
        return pyluxcore.Properties()


def _calc_sun_dir(obj):
    matrix_inv = obj.matrix_world.inverted()
    return [matrix_inv[2][0], matrix_inv[2][1], matrix_inv[2][2]]


def _convert_common_props(exporter, scene, lamp_or_world):
    gain = [x * lamp_or_world.luxcore.gain for x in lamp_or_world.luxcore.rgb_gain]
    importance = lamp_or_world.luxcore.importance
    lightgroup_id = scene.luxcore.lightgroups.get_id_by_name(lamp_or_world.luxcore.lightgroup)
    exporter.lightgroup_cache.add(lightgroup_id)
    return gain, importance, lightgroup_id


def _convert_infinite(definitions, lamp_or_world, scene, transformation=None):
    assert lamp_or_world.luxcore.image is not None

    try:
        filepath = ImageExporter.export(lamp_or_world.luxcore.image,
                                        lamp_or_world.luxcore.image_user,
                                        scene)
    except OSError as error:
        error_context = "Lamp" if isinstance(lamp_or_world, bpy.types.Lamp) else "World"
        msg = '%s "%s": %s' % (error_context, lamp_or_world.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        # Fallback
        definitions["type"] = "constantinfinite"
        # Signal that the image is missing
        definitions["gain"] = [x * lamp_or_world.luxcore.gain for x in MISSING_IMAGE_COLOR]
        return

    definitions["type"] = "infinite"
    definitions["file"] = filepath
    definitions["gamma"] = lamp_or_world.luxcore.gamma
    definitions["sampleupperhemisphereonly"] = lamp_or_world.luxcore.sampleupperhemisphereonly

    if transformation:
        infinite_fix = Matrix.Scale(1.0, 4)
        infinite_fix[0][0] = -1.0  # mirror the hdri map to match Cycles and old LuxBlend
        transformation = utils.matrix_to_list(infinite_fix * transformation.inverted(), scene)
        definitions["transformation"] = transformation


def calc_area_lamp_transformation(lamp, transform_matrix):
    scale_x = Matrix.Scale(lamp.size / 2, 4, (1, 0, 0))
    if lamp.shape == "RECTANGLE":
        scale_y = Matrix.Scale(lamp.size_y / 2, 4, (0, 1, 0))
    else:
        # basically scale_x, but for the y axis (note the last tuple argument)
        scale_y = Matrix.Scale(lamp.size / 2, 4, (0, 1, 0))

    transform_matrix = transform_matrix.copy()
    transform_matrix *= scale_x
    transform_matrix *= scale_y
    return transform_matrix


def _convert_area_lamp(obj, scene, context, luxcore_scene, gain, importance, luxcore_name, dupli_matrix):
    """
    An area light is a plane object with emissive material in LuxCore
    """
    lamp = obj.data
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
        "emission.theta": math.degrees(lamp.luxcore.spread_angle),
        "emission.id": scene.luxcore.lightgroups.get_id_by_name(lamp.luxcore.lightgroup),
        "emission.importance": importance,
        # TODO: maybe transparency (hacky)

        # Note: do not add support for visibility.indirect.* settings, they are useless here
        # because the only sensible setting is to have them enabled, otherwise we lose MIS
    }

    # IES data
    if lamp.luxcore.ies.use:
        try:
            export_ies(mat_definitions, lamp.luxcore.ies, lamp.library, is_meshlight=True)
        except OSError as error:
            msg = 'Lamp "%s": %s' % (obj.name, error)
            scene.luxcore.errorlog.add_warning(msg, obj_name=obj.name)

    mat_props = utils.create_props(mat_prefix, mat_definitions)
    props.Set(mat_props)

    # LuxCore object

    # Copy transformation of area lamp object
    input_matrix = dupli_matrix if dupli_matrix else obj.matrix_world
    transform_matrix = calc_area_lamp_transformation(obj.data, input_matrix)

    if transform_matrix.determinant() == 0:
        # Objects with non-invertible matrices cannot be loaded by LuxCore (RuntimeError)
        # This happens if the lamp size is set to 0
        raise Exception("Area lamp has size 0 (can not be exported)")

    transform = utils.matrix_to_list(transform_matrix, scene, apply_worldscale=True)
    # Only bake the transform into the mesh for final renders (disables instancing which
    # is needed for viewport render so we can move the light object)

    # Instancing just means that we transform the object instead of the mesh
    if utils.use_instancing(obj, scene, context):
        obj_transform = transform
        mesh_transform = None
    else:
        obj_transform = None
        mesh_transform = transform

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
        normals = [
            (0, 0, -1),
            (0, 0, -1),
            (0, 0, -1),
            (0, 0, -1),
        ]
        luxcore_scene.DefineMesh(shape_name, vertices, faces, normals, None, None, None, mesh_transform)

    obj_prefix = "scene.objects." + _get_area_obj_name(luxcore_name) + "."
    obj_definitions = {
        "material": mat_name,
        "shape": shape_name,
        "camerainvisible": not obj.luxcore.visible_to_camera,
    }
    if obj_transform:
        # Use instancing for viewport render so we can interactively move the light
        obj_definitions["transformation"] = obj_transform

    obj_props = utils.create_props(obj_prefix, obj_definitions)
    props.Set(obj_props)

    fake_material_index = 0
    mesh_definition = [luxcore_name, fake_material_index]
    exported_obj = ExportedObject([mesh_definition], luxcore_name)
    return props, exported_obj


def _get_area_obj_name(luxcore_name):
    # Note: we append "000" to the luxcore name here as fake material index because the DefineBlenderMesh
    # function would do the same, and it is expected by other parts of the code.
    return luxcore_name + "000"


def _indirect_light_visibility(definitions, lamp_or_world):
    definitions.update({
        "visibility.indirect.diffuse.enable": lamp_or_world.luxcore.visibility_indirect_diffuse,
        "visibility.indirect.glossy.enable": lamp_or_world.luxcore.visibility_indirect_glossy,
        "visibility.indirect.specular.enable": lamp_or_world.luxcore.visibility_indirect_specular,
    })


def _visibilitymap(definitions, lamp_or_world):
    definitions["visibilitymap.enable"] = lamp_or_world.luxcore.visibilitymap_enable


def export_ies(definitions, ies, library, is_meshlight=False):
    """
    ies is a LuxCoreIESProps PropertyGroup
    """
    prefix = "emission." if is_meshlight else ""
    has_ies = (ies.file_type == "TEXT" and ies.file_text) or (ies.file_type == "PATH" and ies.file_path)

    if not has_ies:
        return False

    definitions[prefix + "flipz"] = ies.flipz
    definitions[prefix + "map.width"] = ies.map_width
    definitions[prefix + "map.height"] = ies.map_height

    # There are two ways to specify IES data: filepath or blob (ascii text)
    if ies.file_type == "TEXT":
        # Blender text block
        text = ies.file_text

        if text:
            blob = text.as_string().encode("ascii")

            if blob:
                definitions[prefix + "iesblob"] = [blob]
    else:
        # File path
        iesfile = ies.file_path

        if iesfile:
            try:
                filepath = utils.get_abspath(iesfile, library, must_exist=True, must_be_existing_file=True)
                definitions[prefix + "iesfile"] = filepath
            except OSError as error:
                # Make the error message more precise
                raise OSError('Could not find .ies file at path "%s" (%s)'
                              % (iesfile, error))

    # has ies
    return True

import bpy
from mathutils import Matrix
import math
from ..bin import pyluxcore
from .. import utils
from .caches.exported_data import ExportedObject, ExportedLight
from .image import ImageExporter
from ..utils.errorlog import LuxCoreErrorLog
from ..nodes.output import get_active_output

WORLD_BACKGROUND_LIGHT_NAME = "__WORLD_BACKGROUND_LIGHT__"
MISSING_IMAGE_COLOR = [1, 0, 1]
TYPES_SUPPORTING_ENVLIGHTCACHE = {"sky2", "infinite", "constantinfinite"}


def convert_light(exporter, obj, obj_key, depsgraph, luxcore_scene, transform, is_viewport_render):
    try:
        luxcore_name = obj_key
        scene = depsgraph.scene_eval

        # If this light was previously defined as an area lamp, delete the area lamp mesh
        luxcore_scene.DeleteObject(_get_area_obj_name(luxcore_name))
        # If this light was previously defined as a light, delete it
        luxcore_scene.DeleteLight(luxcore_name)

        prefix = "scene.lights." + luxcore_name + "."

        if obj.data.luxcore.use_cycles_settings:
            return _convert_cycles_light(exporter, obj, depsgraph, luxcore_scene, transform, is_viewport_render,
                                         luxcore_name, scene, prefix)
        else:
            return _convert_luxcore_light(exporter, obj, depsgraph, luxcore_scene, transform, is_viewport_render,
                                          luxcore_name, scene, prefix)
    except Exception as error:
        msg = 'Light "%s": %s' % (obj.name, error)
        LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
        import traceback
        traceback.print_exc()
        return pyluxcore.Properties(), None


# TODO: warnings, similar to those in the cycles section in ui/light.py
def _convert_cycles_light(exporter, obj, depsgraph, luxcore_scene, transform, is_viewport_render,
                          luxcore_name, scene, prefix):
    definitions = {}
    light = obj.data

    if light.use_nodes:
        LuxCoreErrorLog.add_warning("Cycles light node trees not supported yet", obj.name)

    if light.type != "AREA":
        definitions["gain"] = [light.energy] * 3
        definitions["efficency"] = 0.0
        definitions["power"] = 0.0
        definitions["normalizebycolor"] = False
        definitions["color"] = list(light.color)
        definitions["importance"] = light.luxcore.importance

    if light.type == "POINT":
        definitions["type"] = "point" if light.shadow_soft_size == 0 else "sphere"
        definitions["transformation"] = utils.matrix_to_list(transform)

        if light.shadow_soft_size > 0:
            definitions["radius"] = light.shadow_soft_size
    elif light.type == "SUN":
        sun_dir = _calc_sun_dir(transform)
        distant_dir = [-sun_dir[0], -sun_dir[1], -sun_dir[2]]
        definitions["direction"] = distant_dir
        definitions["color"] = list(light.color)

        half_angle = math.degrees(light.angle) / 2

        if half_angle < 0.05:
            definitions["type"] = "sharpdistant"
        else:
            definitions["type"] = "distant"
            definitions["theta"] = half_angle
            definitions["gain"] = [light.energy * _get_distant_light_normalization_factor(half_angle)] * 3
    elif light.type == "SPOT":
        definitions["type"] = "spot"
        # TODO Cycles has a different falloff, probably needs to be implemented in LuxCore
        definitions["coneangle"] = math.degrees(light.spot_size) / 2
        definitions["conedeltaangle"] = math.degrees(light.spot_size / 2 * light.spot_blend)

        # Position and direction are set by transformation property
        definitions["position"] = [0, 0, 0]
        definitions["target"] = [0, 0, -1]

        spot_fix = Matrix.Rotation(math.radians(-90.0), 4, "Z")
        definitions["transformation"] = utils.matrix_to_list(transform @ spot_fix)

        # Multiplier to reach similar brightness as Cycles, found by eyeballing.
        definitions["gain"] = [light.energy * 0.07] * 3
    elif light.type == "AREA":
        props = pyluxcore.Properties()

        # Calculate gain similar to Cycles (scaling with light surface area)
        transform_matrix = calc_area_light_transformation(light, transform)
        scale = transform_matrix.to_scale()
        gain = light.energy / (scale.x * scale.y)
        # Multiplier to reach similar brightness as Cycles.
        # Found through render comparisons, not super precise.
        gain *= 0.06504

        # Material
        mat_name = luxcore_name + "_AREA_LIGHT_MAT"
        mat_prefix = "scene.materials." + mat_name + "."
        mat_definitions = {
            "type": "matte",
            # Black base material to avoid any bounce light from the mesh
            "kd": [0, 0, 0],
            "emission": list(light.color),
            "emission.gain": [gain] * 3,
            "emission.power": 0.0,
            "emission.efficency": 0.0,
            "emission.normalizebycolor": False,
            "emission.importance": light.luxcore.importance,
            "transparency.shadow": [1, 1, 1],
        }

        mat_props = utils.create_props(mat_prefix, mat_definitions)
        props.Set(mat_props)

        # Object
        use_instancing = utils.use_instancing(obj, scene, is_viewport_render)
        visible_to_camera = False
        obj_props, exported_obj = _create_luxcore_meshlight(obj, transform, use_instancing, luxcore_name,
                                                            luxcore_scene, mat_name, visible_to_camera)
        props.Set(obj_props)
        return props, exported_obj
    else:
        # Can only happen if Blender changes its light types
        raise Exception("Unkown light type", light.type, 'in light "%s"' % obj.name)

    props = utils.create_props(prefix, definitions)
    return props, ExportedLight(luxcore_name)


def _convert_luxcore_light(exporter, obj, depsgraph, luxcore_scene, transform, is_viewport_render,
                           luxcore_name, scene, prefix):
    definitions = {}
    light = obj.data
    sun_dir = _calc_sun_dir(transform)

    # Common light settings shared by all light types
    # Note: these variables are also passed to the area light export function
    gain, importance, lightgroup_id = _convert_common_props(exporter, scene, light)
    definitions["gain"] = apply_exposure(gain, light.luxcore.exposure)
    definitions["importance"] = importance
    definitions["id"] = lightgroup_id

    if light.type == "POINT":
        if light.luxcore.image or light.luxcore.ies.use:
            # mappoint/mapsphere
            definitions["type"] = "mappoint" if light.shadow_soft_size == 0 else "mapsphere"

            has_image = False
            if light.luxcore.image:
                try:
                    filepath = ImageExporter.export(light.luxcore.image,
                                                    light.luxcore.image_user,
                                                    scene)
                    definitions["mapfile"] = filepath
                    definitions["gamma"] = light.luxcore.gamma
                    has_image = True
                except OSError as error:
                    msg = 'Light "%s": %s' % (obj.name, error)
                    LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
                    # Fallback
                    definitions["type"] = "point" if light.shadow_soft_size == 0 else "sphere"
                    # Signal that the image is missing
                    definitions["gain"] = [x * light.luxcore.gain * pow(2, light.luxcore.exposure)
                                           for x in MISSING_IMAGE_COLOR]

            has_ies = False
            try:
                has_ies = export_ies(definitions, light.luxcore.ies, light.library)
            except OSError as error:
                msg = 'Light "%s": %s' % (obj.name, error)
                LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
            finally:
                if not has_ies and not has_image:
                    # Fallback
                    definitions["type"] = "point" if light.shadow_soft_size == 0 else "sphere"
        else:
            # point/sphere
            definitions["type"] = "point" if light.shadow_soft_size == 0 else "sphere"

        _define_brightness(light, definitions)

        # Position is set by transformation property
        definitions["position"] = [0, 0, 0]
        definitions["transformation"] = utils.matrix_to_list(transform)

        if light.shadow_soft_size > 0:
            definitions["radius"] = light.shadow_soft_size

    elif light.type == "SUN":
        distant_dir = [-sun_dir[0], -sun_dir[1], -sun_dir[2]]

        if light.luxcore.light_type == "sun":
            # sun
            definitions["type"] = "sun"
            definitions["dir"] = sun_dir
            definitions["turbidity"] = light.luxcore.turbidity
            definitions["relsize"] = light.luxcore.relsize
        elif light.luxcore.light_type == "hemi":
            # hemi
            if light.luxcore.image:
                _convert_infinite(definitions, light, scene, transform)
            else:
                # Fallback
                definitions["type"] = "constantinfinite"
                definitions["color"] = list(light.luxcore.rgb_gain)
        elif light.luxcore.theta < 0.05:
            # sharpdistant
            definitions["type"] = "sharpdistant"
            definitions["direction"] = distant_dir
            definitions["color"] = list(light.luxcore.rgb_gain)
        else:
            # distant
            definitions["type"] = "distant"
            definitions["direction"] = distant_dir
            definitions["theta"] = light.luxcore.theta
            definitions["color"] = list(light.luxcore.rgb_gain)
            if light.luxcore.normalize_distant:
                normalization_factor = _get_distant_light_normalization_factor(light.luxcore.theta)
                definitions["gain"] = [normalization_factor * x for x in definitions["gain"]]

    elif light.type == "SPOT":
        coneangle = math.degrees(light.spot_size) / 2
        conedeltaangle = math.degrees(light.spot_size / 2 * light.spot_blend)

        if light.luxcore.image:
            # projection
            try:
                definitions["mapfile"] = ImageExporter.export(light.luxcore.image,
                                                              light.luxcore.image_user,
                                                              scene)
                definitions["type"] = "projection"
                definitions["fov"] = coneangle * 2
                definitions["gamma"] = light.luxcore.gamma
            except OSError as error:
                msg = 'Light "%s": %s' % (obj.name, error)
                LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
                # Fallback
                definitions["type"] = "spot"
                # Signal that the image is missing
                definitions["gain"] = [x * light.luxcore.gain * pow(2, light.luxcore.exposure)
                                       for x in MISSING_IMAGE_COLOR]
        else:
            # spot
            definitions["type"] = "spot"
            definitions["coneangle"] = coneangle
            definitions["conedeltaangle"] = conedeltaangle

        _define_brightness(light, definitions)

        # Position and direction are set by transformation property
        definitions["position"] = [0, 0, 0]
        definitions["target"] = [0, 0, -1]

        spot_fix = Matrix.Rotation(math.radians(-90.0), 4, "Z")
        definitions["transformation"] = utils.matrix_to_list(transform @ spot_fix)

    elif light.type == "AREA":
        if light.luxcore.is_laser:
            # laser
            definitions["type"] = "laser"
            definitions["radius"] = light.size / 2

            _define_brightness(light, definitions)

            # Position and direction are set by transformation property
            definitions["position"] = [0, 0, 0]
            definitions["target"] = [0, 0, -1]

            spot_fix = Matrix.Rotation(math.radians(-90.0), 4, "Z")
            definitions["transformation"] = utils.matrix_to_list(transform @ spot_fix)
        else:
            # area (mesh light)
            return _convert_area_light(obj, scene, is_viewport_render, exporter, depsgraph, luxcore_scene, gain,
                                       importance, luxcore_name, transform)

    else:
        # Can only happen if Blender changes its light types
        raise Exception("Unkown light type", light.type, 'in light "%s"' % obj.name)

    _indirect_light_visibility(definitions, light)

    if not is_viewport_render and definitions["type"] in TYPES_SUPPORTING_ENVLIGHTCACHE:
        _envlightcache(definitions, light, scene, is_viewport_render)

    props = utils.create_props(prefix, definitions)
    return props, ExportedLight(luxcore_name)


def convert_world(exporter, world, scene, is_viewport_render):
    try:
        assert isinstance(world, bpy.types.World)
        luxcore_name = WORLD_BACKGROUND_LIGHT_NAME
        prefix = "scene.lights." + luxcore_name + "."

        if world.luxcore.use_cycles_settings:
            definitions = _convert_cycles_world(exporter, scene, world, is_viewport_render)
        else:
            definitions = _convert_luxcore_world(exporter, scene, world, is_viewport_render)

        if definitions:
            return utils.create_props(prefix, definitions)
        else:
            return None
    except Exception as error:
        msg = 'World "%s": %s' % (world.name, error)
        LuxCoreErrorLog.add_warning(msg)
        import traceback
        traceback.print_exc()
        return None


def _convert_cycles_world(exporter, scene, world, is_viewport_render):
    definitions = {
        "importance": world.luxcore.importance,
    }

    if not world.use_nodes:
        color = list(world.color)
        if color == [0, 0, 0]:
            return None
        definitions["type"] = "constantinfinite"
        definitions["color"] = color

    return definitions


def _convert_luxcore_world(exporter, scene, world, is_viewport_render):
    if world.luxcore.light == "none":
        return None

    definitions = {}

    gain, importance, lightgroup_id = _convert_common_props(exporter, scene, world)
    definitions["gain"] = apply_exposure(gain, world.luxcore.exposure)
    definitions["importance"] = importance
    definitions["id"] = lightgroup_id

    light_type = world.luxcore.light
    if light_type == "sky2":
        definitions["type"] = "sky2"
        definitions["ground.enable"] = world.luxcore.ground_enable
        definitions["ground.color"] = list(world.luxcore.ground_color)
        definitions["groundalbedo"] = list(world.luxcore.groundalbedo)

        gain = apply_exposure(gain, world.luxcore.exposure)
        if world.luxcore.sun and world.luxcore.sun.data:
            # Use sun turbidity and direction so the user does not have to keep two values in sync
            definitions["turbidity"] = world.luxcore.sun.data.luxcore.turbidity
            definitions["dir"] = _calc_sun_dir(world.luxcore.sun.matrix_world)
            if world.luxcore.use_sun_gain_for_sky:
                sun = world.luxcore.sun.data
                gain, importance, lightgroup_id = _convert_common_props(exporter, scene, sun)
                gain = apply_exposure(gain, sun.luxcore.exposure)
        else:
            # Use world turbidity
            definitions["turbidity"] = world.luxcore.turbidity

        definitions["gain"] = gain

    elif light_type == "infinite":
        if world.luxcore.image:
            transformation = Matrix.Rotation(world.luxcore.rotation, 4, "Z")
            _convert_infinite(definitions, world, scene, transformation)
        else:
            # Fallback if no image is set
            definitions["type"] = "constantinfinite"
            definitions["color"] = list(world.luxcore.rgb_gain)
    else:
        definitions["type"] = "constantinfinite"
        definitions["color"] = list(world.luxcore.rgb_gain)

    _indirect_light_visibility(definitions, world)

    if not is_viewport_render and definitions["type"] in TYPES_SUPPORTING_ENVLIGHTCACHE:
        _envlightcache(definitions, world, scene, is_viewport_render)

    return definitions


def _get_distant_light_normalization_factor(theta):
    epsilon = 1e-9
    cos_theta_max = min(math.cos(math.radians(theta)), 1 - epsilon)
    return 1 / (2 * math.pi * (1 - cos_theta_max))


def _calc_sun_dir(transform):
    matrix_inv = transform.inverted()
    return [matrix_inv[2][0], matrix_inv[2][1], matrix_inv[2][2]]


def _convert_common_props(exporter, scene, light_or_world):
    gain = [light_or_world.luxcore.gain] * 3
    importance = light_or_world.luxcore.importance
    lightgroup_id = scene.luxcore.lightgroups.get_id_by_name(light_or_world.luxcore.lightgroup)
    exporter.lightgroup_cache.add(lightgroup_id)
    return gain, importance, lightgroup_id


def _convert_infinite(definitions, light_or_world, scene, transformation=None):
    assert light_or_world.luxcore.image is not None

    try:
        filepath = ImageExporter.export(light_or_world.luxcore.image,
                                        light_or_world.luxcore.image_user,
                                        scene)
    except OSError as error:
        error_context = "Light" if isinstance(light_or_world, bpy.types.Light) else "World"
        msg = '%s "%s": %s' % (error_context, light_or_world.name, error)
        LuxCoreErrorLog.add_warning(msg)
        # Fallback
        definitions["type"] = "constantinfinite"
        # Signal that the image is missing
        definitions["gain"] = [x * light_or_world.luxcore.gain for x in MISSING_IMAGE_COLOR]
        return

    definitions["type"] = "infinite"
    definitions["file"] = filepath
    definitions["gamma"] = light_or_world.luxcore.gamma
    definitions["sampleupperhemisphereonly"] = light_or_world.luxcore.sampleupperhemisphereonly

    if transformation:
        infinite_fix = Matrix.Scale(1.0, 4)
        infinite_fix[0][0] = -1.0  # mirror the hdri map to match Cycles and old LuxBlend
        transformation = utils.matrix_to_list(infinite_fix @ transformation.inverted())
        definitions["transformation"] = transformation


def calc_area_light_transformation(light, transform_matrix):
    scale_x = Matrix.Scale(light.size / 2, 4, (1, 0, 0))
    if light.shape in {"RECTANGLE", "ELLIPSE"}:
        scale_y = Matrix.Scale(light.size_y / 2, 4, (0, 1, 0))
    else:
        # basically scale_x, but for the y axis (note the last tuple argument)
        scale_y = Matrix.Scale(light.size / 2, 4, (0, 1, 0))

    transform_matrix = transform_matrix.copy()
    transform_matrix @= scale_x
    transform_matrix @= scale_y
    return transform_matrix


def _get_area_obj_name(luxcore_name):
    fake_material_index = 0
    # The material index after the luxcore_name is expected by ExportedObject
    return luxcore_name + str(fake_material_index)


def _create_luxcore_meshlight(obj, transform, use_instancing, luxcore_name, luxcore_scene,
                              mat_name, visible_to_camera):
    light = obj.data
    transform_matrix = calc_area_light_transformation(light, transform)
    if light.shape not in {"SQUARE", "RECTANGLE"}:
        LuxCoreErrorLog.add_warning("Unsupported area light shape: " + light.shape.title(), obj_name=obj.name)

    if transform_matrix.determinant() == 0:
        # Objects with non-invertible matrices cannot be loaded by LuxCore (RuntimeError)
        # This happens if the light size is set to 0
        raise Exception("Area light has size 0 (can not be exported)")

    transform_list = utils.matrix_to_list(transform_matrix)
    # Only bake the transform into the mesh for final renders (disables instancing which
    # is needed for viewport render so we can move the light object)

    # Instancing just means that we transform the object instead of the mesh
    if use_instancing:
        obj_transform = transform_list
        mesh_transform = None
    else:
        obj_transform = None
        mesh_transform = transform_list

    shape_name = luxcore_name
    if not luxcore_scene.IsMeshDefined(shape_name):
        vertices = [
            (1, 1, 0),
            (1, -1, 0),
            (-1, -1, 0),
            (-1, 1, 0),
        ]
        faces = [
            (0, 1, 2),
            (2, 3, 0),
        ]
        normals = [
            (0, 0, -1),
            (0, 0, -1),
            (0, 0, -1),
            (0, 0, -1),
        ]
        uvs = [
            (1, 1),
            (1, 0),
            (0, 0),
            (0, 1),
        ]
        luxcore_scene.DefineMesh(shape_name, vertices, faces, normals, uvs, None, None, mesh_transform)

    fake_material_index = 0
    # The material index after the luxcore_name is expected by ExportedObject
    obj_prefix = "scene.objects." + _get_area_obj_name(luxcore_name) + "."
    obj_definitions = {
        "material": mat_name,
        "shape": shape_name,
        "camerainvisible": not visible_to_camera,
    }
    if obj_transform:
        # Use instancing for viewport render so we can interactively move the light
        obj_definitions["transformation"] = obj_transform

    obj_props = utils.create_props(obj_prefix, obj_definitions)

    mesh_definition = [luxcore_name, fake_material_index]
    exported_obj = ExportedObject(luxcore_name, [mesh_definition], ["fake_mat_name"],
                                  transform.copy(), visible_to_camera)
    return obj_props, exported_obj


def _convert_area_light(obj, scene, is_viewport_render, exporter, depsgraph, luxcore_scene,
                        gain, importance, luxcore_name, transform):
    """
    An area light is a plane object with emissive material in LuxCore
    """
    light = obj.data
    props = pyluxcore.Properties()

    # Light emitting material
    mat_name = luxcore_name + "_AREA_LIGHT_MAT"
    mat_prefix = "scene.materials." + mat_name + "."
    mat_definitions = {
        "type": "matte",
        # Black base material to avoid any bounce light from the mesh
        "kd": [0, 0, 0],
        "emission": list(light.luxcore.rgb_gain),
        "emission.gain": apply_exposure(gain, light.luxcore.exposure),
        "emission.power": 0.0,
        "emission.efficency": 0.0,
        "emission.normalizebycolor": False,
        "emission.theta": math.degrees(light.luxcore.spread_angle),
        "emission.id": scene.luxcore.lightgroups.get_id_by_name(light.luxcore.lightgroup),
        "emission.importance": importance,
        # TODO: transparency
        # Note: if any of these is disabled, we lose MIS, which can lead to more noise.
        # However, in some rare cases it's needed to disable some of them.
        "visibility.indirect.diffuse.enable": light.luxcore.visibility_indirect_diffuse,
        "visibility.indirect.glossy.enable": light.luxcore.visibility_indirect_glossy,
        "visibility.indirect.specular.enable": light.luxcore.visibility_indirect_specular,
    }

    if light.luxcore.light_unit == "power":
        mat_definitions["emission.power"] = light.luxcore.power
        mat_definitions["emission.efficency"] = light.luxcore.efficacy
        mat_definitions["emission.normalizebycolor"] = light.luxcore.normalizebycolor

        if light.luxcore.efficacy == 0 or light.luxcore.power == 0:
            mat_definitions["emission.gain"] = [0, 0, 0]
        else:
            mat_definitions["emission.gain"] = [1, 1, 1]

    node_tree = light.luxcore.node_tree
    if node_tree:
        tex_props = pyluxcore.Properties()
        tex_name = luxcore_name + "_AREA_LIGHT_TEX"

        active_output = get_active_output(node_tree)

        if active_output is None:
            msg = 'Node tree "%s": Missing active output node' % node_tree.name
            LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
        else:
            # Now export the texture node tree, starting at the output node
            active_output.export(exporter, depsgraph, tex_props, tex_name)
            mat_definitions["emission"] = tex_name
            props.Set(tex_props)

    # IES data
    if light.luxcore.ies.use:
        try:
            export_ies(mat_definitions, light.luxcore.ies, light.library, is_meshlight=True)
        except OSError as error:
            msg = 'light "%s": %s' % (obj.name, error)
            LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)

    mat_props = utils.create_props(mat_prefix, mat_definitions)
    props.Set(mat_props)

    # LuxCore object
    use_instancing = utils.use_instancing(obj, scene, is_viewport_render)
    obj_props, exported_obj = _create_luxcore_meshlight(obj, transform, use_instancing, luxcore_name,
                                                        luxcore_scene, mat_name, obj.luxcore.visible_to_camera)
    props.Set(obj_props)
    return props, exported_obj


def _indirect_light_visibility(definitions, light_or_world):
    definitions.update({
        "visibility.indirect.diffuse.enable": light_or_world.luxcore.visibility_indirect_diffuse,
        "visibility.indirect.glossy.enable": light_or_world.luxcore.visibility_indirect_glossy,
        "visibility.indirect.specular.enable": light_or_world.luxcore.visibility_indirect_specular,
    })


def _envlightcache(definitions, light_or_world, scene, is_viewport_render):
    envlight_cache = scene.luxcore.config.envlight_cache
    enabled = envlight_cache.enabled and light_or_world.luxcore.use_envlight_cache
    definitions["visibilitymapcache.enable"] = enabled
    if enabled:
        # All env. light caches share the same properties (it is very rare to have more than one anyway)
        file_path = utils.get_persistent_cache_file_path(envlight_cache.file_path, envlight_cache.save_or_overwrite,
                                                         is_viewport_render, scene)
        map_width = envlight_cache.map_width
        definitions["visibilitymapcache.map.width"] = map_width
        definitions["visibilitymapcache.map.height"] = map_width / 2
        definitions["visibilitymapcache.map.samplecount"] = envlight_cache.samples
        definitions["visibilitymapcache.map.sampleupperhemisphereonly"] = light_or_world.luxcore.sampleupperhemisphereonly
        definitions["visibilitymapcache.persistent.file"] = file_path


def apply_exposure(gain, exposure):
    return [x * pow(2, exposure) for x in gain]


def _define_brightness(light, definitions):
    definitions["color"] = list(light.luxcore.rgb_gain)

    if light.luxcore.light_unit == "power":
        definitions["efficency"] = light.luxcore.efficacy
        definitions["power"] = light.luxcore.power
        definitions["normalizebycolor"] = light.luxcore.normalizebycolor

        if light.luxcore.efficacy == 0 or light.luxcore.power == 0:
            definitions["gain"] = [0, 0, 0]
        else:
            definitions["gain"] = [1, 1, 1]

    else:
        definitions["efficency"] = 0.0
        definitions["power"] = 0.0
        definitions["normalizebycolor"] = False


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

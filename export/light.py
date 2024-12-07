import bpy
from mathutils import Matrix
import math
import pyluxcore
from .. import utils
from .caches.exported_data import ExportedObject, ExportedLight
from .image import ImageExporter
from ..utils.errorlog import LuxCoreErrorLog
from ..utils import node as utils_node
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


def _convert_cycles_light(exporter, obj, depsgraph, luxcore_scene, transform, is_viewport_render,
                          luxcore_name, scene, prefix):
    definitions = {}
    light = obj.data

    color = list(light.color)
    gain = light.energy

    if light.use_nodes and light.node_tree:
        # Modify color and gain according to node setup
        output_node = light.node_tree.get_output_node("CYCLES")
        if output_node:
            surface_node = utils_node.get_linked_node(output_node.inputs["Surface"])
            if surface_node:
                node_gain = 1
                node_color = [1, 1, 1]

                if surface_node.bl_idname == "ShaderNodeEmission":
                    strength_socket = surface_node.inputs["Strength"]
                    node_gain = strength_socket.default_value
                    if utils_node.get_linked_node(strength_socket):
                        LuxCoreErrorLog.add_warning("Light strength nodes not supported", obj.name)

                    color_socket = surface_node.inputs["Color"]
                    color_node = utils_node.get_linked_node(color_socket)

                    if color_node:
                        if color_node.bl_idname == "ShaderNodeRGB":
                            node_color = list(color_node.outputs[0].default_value)[:3]
                        else:
                            LuxCoreErrorLog.add_warning("Unsupported color node type: " + color_node.bl_idname, obj.name)
                    else:
                         node_color = list(color_socket.default_value)[:3]
                else:
                    LuxCoreErrorLog.add_warning("Unsupported surface node type: " + surface_node.bl_idname, obj.name)

                gain *= node_gain
                color = [a * b for a, b in zip(color, node_color)]

    if light.type == "POINT":
        definitions["type"] = "point" if light.shadow_soft_size == 0 else "sphere"
        definitions["transformation"] = utils.matrix_to_list(transform)

        if light.shadow_soft_size > 0:
            definitions["radius"] = light.shadow_soft_size
    elif light.type == "SUN":
        sun_dir = _calc_sun_dir(transform)
        distant_dir = [-sun_dir[0], -sun_dir[1], -sun_dir[2]]
        definitions["direction"] = distant_dir

        half_angle = math.degrees(light.angle) / 2

        if half_angle < 0.05:
            definitions["type"] = "sharpdistant"
        else:
            definitions["type"] = "distant"
            definitions["theta"] = half_angle
            gain *= _get_distant_light_normalization_factor(half_angle)
    elif light.type == "SPOT":
        if light.shadow_soft_size > 0:
            LuxCoreErrorLog.add_warning("Size (soft shadows) not supported by LuxCore spotlights", obj.name)

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
        gain *= 0.07
    elif light.type == "AREA":
        if light.cycles.is_portal:
            return pyluxcore.Properties(), None

        if light.shape not in {"SQUARE", "RECTANGLE"}:
            LuxCoreErrorLog.add_warning("Unsupported area light shape: " + light.shape.title(), obj.name)

        props = pyluxcore.Properties()

        # Calculate gain similar to Cycles (scaling with light surface area)
        transform_matrix = calc_area_light_transformation(light, transform)
        scale = transform_matrix.to_scale()
        area_gain = gain / (scale.x * scale.y)
        # Multiplier to reach similar brightness as Cycles.
        # Found through render comparisons, not super precise.
        area_gain *= 0.06504

        # Material
        mat_name = luxcore_name + "_AREA_LIGHT_MAT"
        mat_prefix = "scene.materials." + mat_name + "."
        mat_definitions = {
            "type": "matte",
            # Black base material to avoid any bounce light from the mesh
            "kd": [0, 0, 0],
            "emission": color,
            "emission.gain": [area_gain] * 3,
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

    definitions["gain"] = [gain] * 3
    definitions["color"] = color
    definitions["efficency"] = 0.0
    definitions["power"] = 0.0
    definitions["normalizebycolor"] = False
    definitions["importance"] = light.luxcore.importance

    if not light.cycles.cast_shadow:
        LuxCoreErrorLog.add_warning("Cast Shadow is disabled, but unsupported by LuxCore", obj.name)

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

        _define_brightness_and_color(light, definitions)

        # Position is set by transformation property
        definitions["position"] = [0, 0, 0]
        definitions["transformation"] = utils.matrix_to_list(transform)

        if light.shadow_soft_size > 0:
            definitions["radius"] = light.shadow_soft_size

    elif light.type == "SUN":
        distant_dir = [-sun_dir[0], -sun_dir[1], -sun_dir[2]]

        _define_brightness_and_color(light, definitions)

        if light.luxcore.light_type == "sun":
            # sun
            definitions["type"] = "sun"
            definitions["dir"] = sun_dir
            definitions["turbidity"] = light.luxcore.turbidity
            definitions["relsize"] = light.luxcore.relsize

            if light.luxcore.color_mode == "rgb":
                # The sun doesn't support have a "color" property, but its color can be tinted via the gain
                tint_color = light.luxcore.rgb_gain
                for i in range(3):
                    definitions["gain"][i] *= tint_color[i]
        elif light.luxcore.light_type == "hemi":
            # hemi
            if light.luxcore.image:
                _convert_infinite(definitions, light, scene, transform)
            else:
                # Fallback
                definitions["type"] = "constantinfinite"
        elif light.luxcore.theta < 0.05:
            # sharpdistant
            definitions["type"] = "sharpdistant"
            definitions["direction"] = distant_dir
        else:
            # distant
            definitions["type"] = "distant"
            definitions["direction"] = distant_dir
            definitions["theta"] = light.luxcore.theta
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

        _define_brightness_and_color(light, definitions)

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

            _define_brightness_and_color(light, definitions)

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

    # Exterior volume of the light
    volume_node_tree = light.luxcore.volume

    if volume_node_tree:
        luxcore_name = utils.get_luxcore_name(volume_node_tree)
        active_output = get_active_output(volume_node_tree)

        try:
            active_output.export(exporter, depsgraph, props, luxcore_name)
            props.Set(pyluxcore.Property(prefix + "volume", luxcore_name))
        except Exception as error:
            msg = f'Light "{obj.name}": {error}'
            LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)

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

def _define_constantinfinite(definitions, color):
    definitions["type"] = "constantinfinite"
    definitions["color"] = color
    return color != [0, 0, 0]

def _convert_cycles_world(exporter, scene, world, is_viewport_render):
    definitions = {
        "importance": world.luxcore.importance,
    }

    node_tree = world.node_tree

    if not world.use_nodes or not node_tree:
        if not _define_constantinfinite(definitions, list(world.color)):
            return None

    output_node = node_tree.get_output_node("CYCLES")
    if not output_node:
        return None

    surface_node = utils_node.get_linked_node(output_node.inputs["Surface"])
    if not surface_node:
        return None

    if surface_node.bl_idname == "ShaderNodeBackground":
        gain = surface_node.inputs["Strength"].default_value

        color_socket = surface_node.inputs["Color"]
        color_node = utils_node.get_linked_node(color_socket)

        if color_node:
            if color_node.bl_idname == "ShaderNodeRGB":
                color = list(color_node.outputs[0].default_value)[:3]
                if not _define_constantinfinite(definitions, color):
                    return None
            elif color_node.bl_idname == "ShaderNodeTexEnvironment":
                image = color_node.image
                if not image:
                    image_missing = True
                else:
                    try:
                        filepath = ImageExporter.export_cycles_node_reader(image)
                        image_missing = False
                        definitions["type"] = "infinite"
                        definitions["file"] = filepath
                        definitions["gamma"] = 2.2 if image.colorspace_settings.name == "sRGB" else 1

                        # Transformation
                        mapping_node = utils_node.get_linked_node(color_node.inputs["Vector"])
                        if mapping_node:
                            # TODO fix transformation
                            raise NotImplementedError("Mapping node not supported yet")

                            # tex_loc = Matrix.Translation(mapping_node.inputs["Location"].default_value)
                            #
                            # tex_sca = Matrix()
                            # scale = mapping_node.inputs["Scale"].default_value
                            # tex_sca[0][0] = scale.x
                            # tex_sca[1][1] = scale.y
                            # tex_sca[2][2] = scale.z
                            #
                            # # Prevent "singular matrix in matrixinvert" error (happens if a scale axis equals 0)
                            # for i in range(3):
                            #     if tex_sca[i][i] == 0:
                            #         tex_sca[i][i] = 0.0000000001
                            #
                            # rotation = mapping_node.inputs["Rotation"].default_value
                            # tex_rot0 = Matrix.Rotation(rotation.x, 4, "X")
                            # tex_rot1 = Matrix.Rotation(rotation.y, 4, "Y")
                            # tex_rot2 = Matrix.Rotation(rotation.z, 4, "Z")
                            # tex_rot = tex_rot0 @ tex_rot1 @ tex_rot2
                            #
                            # transformation = tex_loc @ tex_rot @ tex_sca
                        else:
                            infinite_fix = Matrix.Scale(1.0, 4)
                            infinite_fix[0][0] = -1.0  # mirror the hdri map to match Cycles and old LuxBlend
                            transformation = infinite_fix @ Matrix.Identity(4).inverted()

                        definitions["transformation"] = utils.matrix_to_list(transformation)
                    except OSError as image_missing:
                        LuxCoreErrorLog.add_warning("World: " + str(image_missing))
                        image_missing = True

                if image_missing:
                    _define_constantinfinite(definitions, MISSING_IMAGE_COLOR)
            elif color_node.bl_idname == "ShaderNodeTexSky":
                if color_node.sky_type != "HOSEK_WILKIE":
                    LuxCoreErrorLog.add_warning("World: Unsupported sky type: " + color_node.sky_type)

                definitions["type"] = "sky2"
                definitions["ground.enable"] = False
                definitions["groundalbedo"] = [color_node.ground_albedo] * 3
                definitions["turbidity"] = color_node.turbidity
                definitions["dir"] = list(color_node.sun_direction)
                # Found by eyeballing, not super precise
                gain *= 0.000014
        else:
            # No color node linked
            definitions["type"] = "constantinfinite"
            # Alpha not supported
            color = list(color_socket.default_value)[:3]
            if not _define_constantinfinite(definitions, color):
                return None
    else:
        raise Exception("Unsupported node type:", surface_node.bl_idname)

    if gain == 0:
        return None

    definitions["gain"] = [gain] * 3
    return definitions


def _convert_luxcore_world(exporter, scene, world, is_viewport_render):
    if world.luxcore.light == "none":
        return None

    definitions = {}

    gain, importance, lightgroup_id = _convert_common_props(exporter, scene, world)
    definitions["gain"] = apply_exposure(gain, world.luxcore.exposure)
    definitions["importance"] = importance
    definitions["id"] = lightgroup_id

    if world.luxcore.color_mode == "rgb":
        tint_color = list(world.luxcore.rgb_gain)
    elif world.luxcore.color_mode == "temperature":
        tint_color = [1, 1, 1]
        definitions["temperature"] = world.luxcore.temperature
        definitions["temperature.normalize"] = True
    else:
        raise Exception("Unkown color mode")

    light_type = world.luxcore.light
    if light_type == "sky2":
        definitions["type"] = "sky2"
        definitions["ground.enable"] = world.luxcore.ground_enable
        definitions["ground.color"] = list(world.luxcore.ground_color)
        definitions["groundalbedo"] = list(world.luxcore.groundalbedo)

        if world.luxcore.sun and world.luxcore.sun.data:
            # Use sun turbidity and direction so the user does not have to keep two values in sync
            definitions["turbidity"] = world.luxcore.sun.data.luxcore.turbidity
            definitions["dir"] = _calc_sun_dir(world.luxcore.sun.matrix_world)
            if world.luxcore.use_sun_gain_for_sky:
                sun = world.luxcore.sun.data
                gain, _, _ = _convert_common_props(exporter, scene, sun)
                definitions["gain"] = apply_exposure(gain, sun.luxcore.exposure)
        else:
            # Use world turbidity
            definitions["turbidity"] = world.luxcore.turbidity
        
        for i in range(3):
            definitions["gain"][i] *= tint_color[i]

    elif light_type == "infinite":
        if world.luxcore.image:
            transformation = Matrix.Rotation(world.luxcore.rotation, 4, "Z")
            _convert_infinite(definitions, world, scene, transformation)
            for i in range(3):
                definitions["gain"][i] *= tint_color[i]
        else:
            # Fallback if no image is set
            definitions["type"] = "constantinfinite"
            definitions["color"] = tint_color
    else:
        definitions["type"] = "constantinfinite"
        definitions["color"] = tint_color

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
    if isinstance(light_or_world, bpy.types.Light):
        if light_or_world.type == "SUN" and light_or_world.luxcore.light_type == "sun":
            raw_gain = light_or_world.luxcore.sun_sky_gain
        else:
            raw_gain = light_or_world.luxcore.gain
    else:
        # It's a bpy.types.World
        if light_or_world.luxcore.light == "sky2":
            raw_gain = light_or_world.luxcore.sun_sky_gain
        else:
            raw_gain = light_or_world.luxcore.gain

    gain = [raw_gain] * 3


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
        # TODO one axis still not correct
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
        "emission.gain.normalizebycolor": False,
        "emission.power": 0.0,
        "emission.efficency": 0.0,
        "emission.normalizebycolor": False,
        "emission.theta": math.degrees(light.luxcore.spread_angle),
        "emission.id": scene.luxcore.lightgroups.get_id_by_name(light.luxcore.lightgroup),
        "emission.importance": importance,
        "transparency.shadow": [0, 0, 0] if light.luxcore.visible else [1, 1, 1],
        # Note: if any of these is disabled, we lose MIS, which can lead to more noise.
        # However, in some rare cases it's needed to disable some of them.
        "visibility.indirect.diffuse.enable": light.luxcore.visibility_indirect_diffuse,
        "visibility.indirect.glossy.enable": light.luxcore.visibility_indirect_glossy,
        "visibility.indirect.specular.enable": light.luxcore.visibility_indirect_specular,
    }

    if light.luxcore.color_mode == "rgb":
        mat_definitions["emission"] = list(light.luxcore.rgb_gain)
    elif light.luxcore.color_mode == "temperature":
        mat_definitions["emission"] = [1, 1, 1]
        mat_definitions["emission.temperature"] = light.luxcore.temperature
        mat_definitions["emission.temperature.normalize"] = True
    else:
        raise Exception("Unkown color mode")

    if light.luxcore.light_unit == "power":
        mat_definitions["emission.power"] = light.luxcore.power / ( 2 * math.pi * (1 - math.cos(light.luxcore.spread_angle/2) ))
        mat_definitions["emission.efficency"] = light.luxcore.efficacy
        mat_definitions["emission.normalizebycolor"] = light.luxcore.normalizebycolor

        if light.luxcore.efficacy == 0 or light.luxcore.power == 0:
            mat_definitions["emission.gain"] = [0, 0, 0]
        else:
            mat_definitions["emission.gain"] = [1, 1, 1]

    if light.luxcore.light_unit == "lumen":
        mat_definitions["emission.power"] = light.luxcore.lumen / ( 2 * math.pi * (1 - math.cos(light.luxcore.spread_angle/2) ))
        mat_definitions["emission.efficency"] = 1.0
        mat_definitions["emission.normalizebycolor"] = light.luxcore.normalizebycolor
        if light.luxcore.lumen == 0:
            mat_definitions["emission.gain"] = [0, 0, 0]
        else:
            mat_definitions["emission.gain"] = [1, 1, 1]
    
    if light.luxcore.light_unit == "candela":
        if light.luxcore.per_square_meter:
            mat_definitions["emission.power"] = 0.0
            mat_definitions["emission.efficency"] = 0.0
            mat_definitions["emission.gain"] = [light.luxcore.candela] * 3
            mat_definitions["emission.gain.normalizebycolor"] = light.luxcore.normalizebycolor
        else:
            # Multiply with pi to match brightness with other light types
            mat_definitions["emission.power"] = light.luxcore.candela * math.pi
            mat_definitions["emission.efficency"] = 1.0
            mat_definitions["emission.normalizebycolor"] = light.luxcore.normalizebycolor
            if light.luxcore.candela == 0:
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
    visible_to_camera = obj.luxcore.visible_to_camera and light.luxcore.visible
    obj_props, exported_obj = _create_luxcore_meshlight(obj, transform, use_instancing, luxcore_name,
                                                        luxcore_scene, mat_name, visible_to_camera)
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
        definitions["visibilitymapcache.map.quality"] = envlight_cache.quality
        # Automatically chosen by LuxCore according to the quality and HDRI map size
        definitions["visibilitymapcache.map.tilewidth"] = 0
        definitions["visibilitymapcache.map.tileheight"] = 0
        definitions["visibilitymapcache.map.tilesamplecount"] = 0

        definitions["visibilitymapcache.map.sampleupperhemisphereonly"] = light_or_world.luxcore.sampleupperhemisphereonly

        file_path = utils.get_persistent_cache_file_path(envlight_cache.file_path, envlight_cache.save_or_overwrite,
                                                         is_viewport_render, scene)
        definitions["visibilitymapcache.persistent.file"] = file_path


def apply_exposure(gain, exposure):
    return [x * pow(2, exposure) for x in gain]


def _define_brightness_and_color(light, definitions):
    # Brightness
    normalize_by_color = light.luxcore.normalizebycolor
    gain = None

    if light.luxcore.light_unit == "power":
        efficency = light.luxcore.efficacy
        power = light.luxcore.power

        if light.luxcore.efficacy == 0 or light.luxcore.power == 0:
            gain = [0, 0, 0]
        else:
            gain = [1, 1, 1]

    elif light.luxcore.light_unit == "lumen":
        efficency = 1.0

        if light.type == "SPOT":
            power = light.luxcore.lumen
        else:
            power = light.luxcore.lumen

        if light.luxcore.lumen == 0:
            gain = [0, 0, 0]
        else:
            gain = [1, 1, 1]
    
    elif light.luxcore.light_unit == "candela":
        efficency = 1.0

        if light.type == "SPOT":
            power = light.luxcore.candela * 2 * math.pi * (1 - math.cos(light.spot_size/2))
        else:
            power = light.luxcore.candela * 4 * math.pi

        if light.luxcore.candela == 0:
            gain = [0, 0, 0]
        else:
            gain = [1, 1, 1]
        
    elif light.luxcore.light_unit == "artistic":
        efficency = 0.0
        power = 0.0
        normalize_by_color = False
    else:
        raise Exception("Unknown light unit")

    definitions["efficency"] = efficency
    definitions["power"] = power
    definitions["normalizebycolor"] = normalize_by_color
    if gain is not None:
        definitions["gain"] = gain

    # Color
    if light.luxcore.color_mode == "rgb":
        definitions["color"] = list(light.luxcore.rgb_gain)
    elif light.luxcore.color_mode == "temperature":
        definitions["color"] = [1, 1, 1]
        definitions["temperature"] = light.luxcore.temperature
        definitions["temperature.normalize"] = True
    else:
        raise Exception("Unkown color mode")


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

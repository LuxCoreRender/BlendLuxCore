from enum import Enum
from time import sleep
from mathutils import Matrix
from ..bin import pyluxcore
from .. import utils
from .. import export
from ..draw.final import FrameBufferFinal
from ..utils.log import LuxCoreLog

"""
Note: you can find the Blender preview scene in the sources at this path:
blender/release/datafiles/preview.blend
"""

# Diameter of the default sphere, in meters
DEFAULT_SPHERE_SIZE = 0.1

class PreviewType(Enum):
    NONE = 0
    MATERIAL = 1


# We use this as pyluxcore log handler to avoid spamming the console
def no_log_output(message):
    pass


def render(engine, depsgraph):
    scene = depsgraph.scene_eval    
    width, height = utils.calc_filmsize(scene)

    if max(width, height) <= 96:
        # We do not render thumbnails
        return

    pyluxcore.SetLogHandler(no_log_output)
    engine.exporter = export.Exporter(scene)
    preview_type, active_mat = _get_preview_settings(engine.exporter, depsgraph)

    if preview_type == PreviewType.MATERIAL and not active_mat is None:
        engine.session = _export_mat_scene(engine, depsgraph, active_mat)
    else:
        print("Unsupported preview type")
        return enable_log_output()


    engine.framebuffer = FrameBufferFinal(scene)
    engine.session.Start()

    while True:
        try:
            engine.session.UpdateStats()
        except RuntimeError as error:
            print("Error during UpdateStats():", error)

        if engine.session.HasDone():
            break

        stats = engine.session.GetStats()
        samples = stats.Get("stats.renderengine.pass").GetInt()
        if (samples > 2 and samples < 10) or (samples > 0 and samples % 10 == 0):
            engine.framebuffer.draw(engine, engine.session, scene, False)
        sleep(1 / 30)

        if engine.test_break():
            # Abort as fast as possible, without drawing the framebuffer again
            engine.session.Stop()
            return enable_log_output()

    engine.framebuffer.draw(engine, engine.session, scene, True)
    engine.session.Stop()
    enable_log_output()


def enable_log_output():
    # Re-enable the log output
    pyluxcore.SetLogHandler(LuxCoreLog.add)


def _export_mat_scene(engine, depsgraph, active_mat):    
    exporter = engine.exporter
    scene = depsgraph.scene_eval

    # The diameter that the preview objects should have, in meters
    size = active_mat.luxcore.preview.size
    worldscale = size / DEFAULT_SPHERE_SIZE
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = worldscale

    scene_props = pyluxcore.Properties()
    luxcore_scene = pyluxcore.Scene()

    # The world sphere uses different lights and render settings
    is_world_sphere = active_mat.use_preview_world

    # Camera
    cam_props = export.camera.convert(exporter, scene)

    # Apply zoom
    field_of_view = cam_props.Get("scene.camera.fieldofview").GetFloat()
    zoom = active_mat.luxcore.preview.zoom
    cam_props.Set(pyluxcore.Property("scene.camera.fieldofview", field_of_view / zoom))
    luxcore_scene.Parse(cam_props)

    # Objects    
    for index, dg_obj_instance in enumerate(depsgraph.object_instances, start=1):
        obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
        if not exporter.object_cache2._is_visible(dg_obj_instance, obj):
            continue

        # Don't export lights and floor from preview scene
        if not (obj.type == 'LIGHT' or obj.name == 'Floor'):           
            exporter.object_cache2._convert_obj(exporter, dg_obj_instance, obj, depsgraph,
                                                luxcore_scene, scene_props, False)
    
    # Lights (either two area lights or a sun+sky setup)
    _create_lights(scene, luxcore_scene, scene_props, is_world_sphere)

##  #TODO: Decide if the ground plane should be visible with world sphere enabled
##    if not is_world_sphere:
##        _create_backplates(scene, luxcore_scene, scene_props)
    # Ground plane
    _create_backplates(scene, luxcore_scene, scene_props)

    luxcore_scene.Parse(scene_props)

    # Session
    config_props = _create_config(scene, is_world_sphere)
    renderconfig = pyluxcore.RenderConfig(config_props, luxcore_scene)
    session = pyluxcore.RenderSession(renderconfig)
    
    return session


##def _export_plane_scene(exporter, scene, mat, props, luxcore_scene):
##    # The default plane from the Blender preview scene is ugly (wrong scale and UVs), so we make our own.
##    # A quadratic texture (with UV mapping) is tiled exactly 2 times in horizontal directon on this plane,
##    # so it's also a nice tiling preview
##
##    lux_mat_name, mat_props = export.material.convert(exporter, mat, scene, None)
##    props.Set(mat_props)
##
##    worldscale = utils.get_worldscale(scene, as_scalematrix=False)
##
##    mesh_name = "mat_preview_planemesh"
##    size_z_raw = 2
##    size_z = size_z_raw * worldscale
##    size_x = size_z_raw * 2 * worldscale
##    ypos = 0
##    zpos = 2 * worldscale
##    vertices = [
##        (-size_x / 2, ypos, zpos - size_z / 2),
##        (size_x / 2, ypos, zpos - size_z / 2),
##        (size_x / 2, ypos, zpos + size_z / 2),
##        (-size_x / 2, ypos, zpos + size_z / 2),
##    ]
##    faces = [
##        (0, 1, 2),
##        (2, 3, 0)
##    ]
##    uv = [
##        (1, 2),
##        (1, 0),
##        (0, 0),
##        (0, 2)
##    ]
##    luxcore_scene.DefineMesh(mesh_name, vertices, faces, None, uv, None, None)
##    # Create object
##    obj_name = "mat_preview_planeobj"
##    props.Set(pyluxcore.Property("scene.objects." + obj_name + ".ply", mesh_name))
##    props.Set(pyluxcore.Property("scene.objects." + obj_name + ".material", lux_mat_name))


def _create_lights(scene, luxcore_scene, props, is_world_sphere):
    if is_world_sphere:
        props.Set(pyluxcore.Property("scene.lights.sky.type", "sky2"))
        props.Set(pyluxcore.Property("scene.lights.sky.gain", [.00003] * 3))
        # Building the visibility map and not needed in an open scene
        props.Set(pyluxcore.Property("scene.lights.sky.visibilitymap.enable", False))

        props.Set(pyluxcore.Property("scene.lights.sun.type", "sun"))
        props.Set(pyluxcore.Property("scene.lights.sun.dir", [-0.6, -1, 0.9]))
        props.Set(pyluxcore.Property("scene.lights.sun.gain", [.00003] * 3))
        # Avoid fireflies
        props.Set(pyluxcore.Property("scene.lights.sun.visibility.indirect.specular.enable", False))
    else:
        # Key light
        color_key = [70] * 3
        position_key = [-10, -15, 10]
        rotation_key = Matrix(((0.8578430414199829, 0.22907057404518127, -0.4600348174571991),
                               (-0.5139118432998657, 0.3823741674423218, -0.7679092884063721),
                               (2.1183037546279593e-09, 0.8951629400253296, 0.44573909044265747)))
        scale_key = 2
        _create_area_light(scene, luxcore_scene, props, "key", color_key,
                           position_key, rotation_key, scale_key)

        # Fill light
        color_fill = [1.5] * 3
        position_fill = [20, -30, 12]
        rotation_fill = Matrix(((0.6418147087097168, -0.3418193459510803, 0.6864644289016724),
                                (0.766859769821167, 0.2860819101333618, -0.5745287537574768),
                                (2.1183037546279593e-09, 0.8951629400253296, 0.44573909044265747)))
        scale_fill = 12
        _create_area_light(scene, luxcore_scene, props, "fill", color_fill,
                           position_fill, rotation_fill, scale_fill)


def _create_area_light(scene, luxcore_scene, props, name, color, position, rotation_matrix, scale):
    mat_name = name + "_mat"
    mesh_name = name + "_mesh"

    # Material
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".type", ["matte"]))
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".kd", [0.0] * 3))
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".emission", color))
    # assign material to object
    props.Set(pyluxcore.Property("scene.objects." + name + ".material", [mat_name]))

    scale_matrix = Matrix()
    scale_matrix[0][0] = scale
    scale_matrix[1][1] = scale
    rotation_matrix.resize_4x4()
    transform_matrix = Matrix()
    transform_matrix[0][3] = position[0]
    transform_matrix[1][3] = position[1]
    transform_matrix[2][3] = position[2]

    mat = transform_matrix @ rotation_matrix @ scale_matrix
    transform = utils.matrix_to_list(mat, scene, apply_worldscale=True)

    # add mesh
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
    luxcore_scene.DefineMesh(mesh_name, vertices, faces, None, None, None, None, transform)
    # assign mesh to object
    props.Set(pyluxcore.Property("scene.objects." + name + ".shape", [mesh_name]))
    return props


def _create_backplates(scene, luxcore_scene, props):
    worldscale = utils.get_worldscale(scene, as_scalematrix=False)

    # Ground plane
    size = worldscale
    zpos = 0.0
    vertices = [
        (size, size, zpos),
        (size, -size, zpos),
        (-size, -size, zpos),
        (-size, size, zpos)
    ]
    faces = [
        (0, 1, 2),
        (2, 3, 0)
    ]
    _create_checker_plane(luxcore_scene, props, "ground_plane", vertices, faces, worldscale)


def _create_checker_plane(luxcore_scene, props, name, vertices, faces, worldscale):
    mesh_name = name + "_mesh"
    mat_name = name + "_mat"
    tex_name = name + "_tex"

    # Mesh
    luxcore_scene.DefineMesh(mesh_name, vertices, faces, None, None, None, None)
    # Texture
    # (we scale the default sphere to be 10cm by default and we want the squares to be 5cm in size)
    checker_size = 5
    checker_trans = [checker_size, 0, 0, 0, 0, checker_size, 0, 0, 0, 0, checker_size, 0, 0, 0, 0, 1]
    props.Set(pyluxcore.Property("scene.textures." + tex_name + ".type", "checkerboard3d"))
    props.Set(pyluxcore.Property("scene.textures." + tex_name + ".texture1", 0.7))
    props.Set(pyluxcore.Property("scene.textures." + tex_name + ".texture2", 0.2))
    props.Set(pyluxcore.Property("scene.textures." + tex_name + ".mapping.type", "globalmapping3d"))
    props.Set(pyluxcore.Property("scene.textures." + tex_name + ".mapping.transformation", checker_trans))
    # Material
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".type", "matte"))
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".kd", tex_name))
    # Invisible for indirect diffuse rays to eliminate fireflies
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".visibility.indirect.diffuse.enable", False))

    # Object
    props.Set(pyluxcore.Property("scene.objects." + name + ".shape", mesh_name))
    props.Set(pyluxcore.Property("scene.objects." + name + ".material", mat_name))


def _create_config(scene, is_world_sphere):
    prefix = ""

    width, height = utils.calc_filmsize(scene)

    if is_world_sphere:
        total_depth = 4
        diffuse_depth = 1
        specular_depth = 3
    else:
        total_depth = 8
        diffuse_depth = 3
        specular_depth = 4

    definitions = {
        "film.width": width,
        "film.height": height,

        "renderengine.type": "PATHCPU",
        "sampler.type": "SOBOL",
        # Focus as much as possible on the preview object
        "sampler.sobol.adaptive.strength": 0.95,

        "path.pathdepth.total": total_depth,
        "path.pathdepth.diffuse": diffuse_depth,
        "path.pathdepth.glossy": 3,
        "path.pathdepth.specular": specular_depth,

        "path.clamping.variance.maxvalue": 3,

        "film.filter.type": "BLACKMANHARRIS",
        "film.filter.width": 1.5,

        # The overhead of the kernel compilation is not worth it in our tiny preview
        "film.opencl.enable": False,
        # Imagepipeline
        "film.imagepipeline.0.type": "TONEMAP_LINEAR",
        "film.imagepipeline.0.scale": 1.0,

        # Preview quality
        "batch.halttime": 6,

        "batch.haltthreshold": 8 / 256,
        "batch.haltthreshold.warmup": 3,
        "batch.haltthreshold.step": 3,
        "batch.haltthreshold.filter.enable": False,
    }

    return utils.create_props(prefix, definitions)


def _convert_obj(exporter, obj, scene, luxcore_scene, props):
    obj_props, exported_obj = export.blender_object.convert(exporter, obj, scene, None, luxcore_scene, update_mesh=True)

    for psys in obj.particle_systems:
        settings = psys.settings
        if settings.type == "HAIR" and settings.render_type == "PATH":
            # Make the strands in strand preview mode thicker so they are visible
            settings.luxcore.hair.hair_size = 0.05
            settings.luxcore.hair.tesseltype = "solid"
            export.hair.convert_hair(exporter, obj, psys, luxcore_scene, scene)

    props.Set(obj_props)


def _get_preview_settings(exporter, depsgraph):    
    # Iterate through the preview scene, finding objects with materials attached
    objects = []
    for dg_obj_instance in depsgraph.object_instances:        
        obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
        if not exporter.object_cache2._is_visible(dg_obj_instance, obj):
            continue

        if obj.name.startswith("preview"):
            active_mat = obj.active_material
            objects.append(obj)

    if objects:
        return PreviewType.MATERIAL, active_mat

    return PreviewType.NONE, None

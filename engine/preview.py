from enum import Enum
from time import sleep
from os.path import dirname, realpath
from mathutils import Matrix
from ..bin import pyluxcore
from .. import utils
from .. import export
from ..draw.final import FrameBufferFinal
from ..utils.log import LuxCoreLog

DEFAULT_SPHERE_SIZE = 0.1

class PreviewType(Enum):
    NONE = 0
    MATERIAL = 1

def no_log_output(message):
    pass

def enable_log_output():
    pyluxcore.SetLogHandler(LuxCoreLog.add)

def render(engine, depsgraph):
    scene = depsgraph.scene_eval
    width, height = utils.calc_filmsize(scene)

    if max(width, height) <= 96:
        return

    pyluxcore.SetLogHandler(no_log_output)
    engine.exporter = export.Exporter()
    engine.exporter.scene = scene
    preview_type, active_mat = _get_preview_settings(depsgraph)

    if preview_type == PreviewType.MATERIAL and active_mat:
        engine.session = _export_mat_scene(engine, depsgraph, active_mat)
    else:
        print("Unsupported preview type")
        return enable_log_output()

    engine.framebuffer = FrameBufferFinal(scene)
    engine.session.Start()

    while not engine.session.HasDone():
        try:
            engine.session.UpdateStats()
        except RuntimeError as error:
            print("Error during UpdateStats():", error)

        stats = engine.session.GetStats()
        samples = stats.Get("stats.renderengine.pass").GetInt()

        if 2 < samples < 10 or (samples > 0 and samples % 10 == 0):
            engine.framebuffer.draw(engine, engine.session, scene, False)
        
        sleep(1 / 30)

        if engine.test_break():
            engine.session.Stop()
            return enable_log_output()

    engine.framebuffer.draw(engine, engine.session, scene, True)
    engine.session.Stop()
    engine.exporter.scene = None
    enable_log_output()

def _export_mat_scene(engine, depsgraph, active_mat):
    from ..export.caches.exported_data import ExportedObject
    from ..export.caches.object_cache import export_material, define_shapes

    exporter = engine.exporter
    scene = depsgraph.scene_eval
    scene_props = pyluxcore.Properties()
    luxcore_scene = pyluxcore.Scene()

    is_world_sphere = active_mat.use_preview_world

    cam_props = export.camera.convert(exporter, scene, depsgraph)
    field_of_view = cam_props.Get("scene.camera.fieldofview").GetFloat()

    cam_props.Set(pyluxcore.Property("scene.camera.autovolume.enable", 0))
    zoom = active_mat.luxcore.preview.zoom
    cam_props.Set(pyluxcore.Property("scene.camera.fieldofview", field_of_view / zoom))
    luxcore_scene.Parse(cam_props)

    for dg_obj_instance in depsgraph.object_instances:
        obj = dg_obj_instance.object

        if not utils.is_instance_visible(dg_obj_instance, obj, None):
            continue

        if obj.name in {"CurveCircle.002", "preview_shaderball.003", "Floor"} or obj.type == "LIGHT":
            continue

        if obj.name == "preview_shaderball":
            is_viewport_render = False
            obj_key = "Preview_LuxBall_Object"
            mesh_key = "Preview_LuxBall_Mesh"
            mesh_definitions = []
            props = pyluxcore.Properties()
            filepath = dirname(dirname(realpath(__file__))) + "/preview_scene/LuxCore_preview.ply"

            prefix = "scene.shapes." + mesh_key + "."
            props.Set(pyluxcore.Property(prefix + "type", "mesh"))
            props.Set(pyluxcore.Property(prefix + "ply", filepath))
            mesh_definitions.append((mesh_key, 0))
            scene_props.Set(props)

            mat_names = []
            for idx, (shape_name, mat_index) in enumerate(mesh_definitions):
                shape = shape_name
                lux_mat_name, mat_props, node_tree = export_material(obj, mat_index, exporter, depsgraph, is_viewport_render)
                scene_props.Set(mat_props)
                mat_names.append(lux_mat_name)

                if node_tree:
                    shape = define_shapes(shape, node_tree, exporter, depsgraph, scene_props)

                mesh_definitions[idx] = [shape, mat_index]

            exported_obj = ExportedObject(obj_key, mesh_definitions, mat_names, None, True)

            scene_props.Set(exported_obj.get_props())
            exporter.object_cache2.exported_objects[obj_key] = exported_obj
        else:
            exporter.object_cache2._convert_obj(exporter, dg_obj_instance, obj, depsgraph, luxcore_scene, scene_props, False)

    for shape_key in scene_props.GetAllUniqueSubNames("scene.shapes"):
        shape_props = scene_props.GetAllProperties(shape_key)
        if shape_props.Get(shape_key + ".type", [""]).GetString() == "subdiv":
            max_level = shape_props.Get(shape_key + ".maxlevel", [0]).GetInt()
            shape_props.Set(pyluxcore.Property(shape_key + ".maxlevel", min(max_level, 1)))
            scene_props.Set(shape_props)

    _create_lights(scene, luxcore_scene, scene_props, is_world_sphere)

    if not is_world_sphere:
        _create_backplates(luxcore_scene, scene_props)
    _create_ground(luxcore_scene, scene_props)

    luxcore_scene.Parse(scene_props)

    config_props = _create_config(scene)
    renderconfig = pyluxcore.RenderConfig(config_props, luxcore_scene)
    session = pyluxcore.RenderSession(renderconfig)
    return session

def _create_lights(scene, luxcore_scene, props, is_world_sphere):
    if is_world_sphere:
        props.Set(pyluxcore.Property("scene.lights.sky.type", "sky2"))
        props.Set(pyluxcore.Property("scene.lights.sky.gain", [.00003] * 3))
        props.Set(pyluxcore.Property("scene.lights.sky.visibilitymap.enable", False))

        props.Set(pyluxcore.Property("scene.lights.sun.type", "sun"))
        props.Set(pyluxcore.Property("scene.lights.sun.dir", [-0.6, -1, 0.9]))
        props.Set(pyluxcore.Property("scene.lights.sun.gain", [.00003] * 3))
        props.Set(pyluxcore.Property("scene.lights.sun.visibility.indirect.specular.enable", False))
    else:
        _create_area_light(scene, luxcore_scene, props, "key", [80] * 3, [4.5, -6, 5], Matrix(), 1)
        _create_area_light(scene, luxcore_scene, props, "fill", [4] * 3, [-5.5, -2.5, 2.5], Matrix(), 2, False)

def _create_area_light(scene, luxcore_scene, props, name, color, position, rotation_matrix, scale, visible=True):
    mat_name = name + "_mat"
    mesh_name = name + "_mesh"
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".type", ["matte"]))
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".kd", [0.0] * 3))
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".emission", color))
    props.Set(pyluxcore.Property("scene.objects." + name + ".material", [mat_name]))
    props.Set(pyluxcore.Property("scene.objects." + name + ".camerainvisible", not visible))

    scale_matrix = Matrix.Scale(scale, 4)
    transform_matrix = Matrix.Translation(position) @ rotation_matrix @ scale_matrix

    mat = transform_matrix
    transform = utils.matrix_to_list(mat)

    vertices = [(1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0)]
    faces = [(0, 1, 2), (2, 3, 0)]

    luxcore_scene.DefineMesh(mesh_name, vertices, faces, None, None, None, None, transform)
    props.Set(pyluxcore.Property("scene.objects." + name + ".shape", [mesh_name]))
    return props

def _create_backplates(luxcore_scene, props):
    size = 20
    zpos = 0.0
    vertices = [(size, size, zpos), (size, -size, zpos), (-size, -size, zpos), (-size, size, zpos),
                (size, size, 0.5*size), (size, -size, 0.5*size), (-size, -size, 0.5*size), (-size, size, 0.5*size)]
    faces = [(6, 5, 4), (4, 7, 6), (2, 3, 7), (7, 6, 2), (2, 6, 5), (5, 1, 2), (7, 3, 0), (0, 4, 7), (4, 0, 1), (1, 5, 4)]
    _create_walls(luxcore_scene, props, "walls", vertices, faces)

def _create_ground(luxcore_scene, props):
    size = 20
    zpos = 0.0
    vertices = [(size, size, zpos), (size, -size, zpos), (-size, -size, zpos), (-size, size, zpos)]
    faces = [(0, 1, 2), (2, 3, 0)]
    _create_checker_plane(luxcore_scene, props, "ground_plane", vertices, faces)

def _create_checker_plane(luxcore_scene, props, name, vertices, faces):
    mesh_name = name + "_mesh"
    mat_name = name + "_mat"
    tex_name = name + "_tex"

    luxcore_scene.DefineMesh(mesh_name, vertices, faces, None, None, None, None)
    checker_size = 5
    checker_trans = [checker_size, 0, 0, 0, 0, checker_size, 0, 0, 0, 0, checker_size, 0, 0, 0, 0, 1]
    props.Set(pyluxcore.Property("scene.textures." + tex_name + ".type", "checkerboard3d"))
    props.Set(pyluxcore.Property("scene.textures." + tex_name + ".texture1", 0.7))
    props.Set(pyluxcore.Property("scene.textures." + tex_name + ".texture2", 0.2))
    props.Set(pyluxcore.Property("scene.textures." + tex_name + ".mapping.type", "globalmapping3d"))
    props.Set(pyluxcore.Property("scene.textures." + tex_name + ".mapping.transformation", checker_trans))
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".type", "matte"))
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".kd", tex_name))
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".visibility.indirect.diffuse.enable", False))
    props.Set(pyluxcore.Property("scene.objects." + name + ".shape", mesh_name))
    props.Set(pyluxcore.Property("scene.objects." + name + ".material", mat_name))

def _create_walls(luxcore_scene, props, name, vertices, faces):
    mesh_name = name + "_mesh"
    mat_name = name + "_mat"
    luxcore_scene.DefineMesh(mesh_name, vertices, faces, None, None, None, None)
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".type", "matte"))
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".kd", 0.7))
    props.Set(pyluxcore.Property("scene.materials." + mat_name + ".visibility.indirect.diffuse.enable", False))
    props.Set(pyluxcore.Property("scene.objects." + name + ".shape", mesh_name))
    props.Set(pyluxcore.Property("scene.objects." + name + ".material", mat_name))

def _create_config(scene):
    prefix = ""
    width, height = utils.calc_filmsize(scene)

    definitions = {
        "film.width": width,
        "film.height": height,
        "renderengine.type": "PATHCPU",
        "sampler.type": "SOBOL",
        "sampler.sobol.adaptive.strength": 0.95,
        "path.pathdepth.total": 12,
        "path.pathdepth.diffuse": 4,
        "path.pathdepth.glossy": 5,
        "path.pathdepth.specular": 5,
        "path.clamping.variance.maxvalue": 3,
        "film.filter.type": "BLACKMANHARRIS",
        "film.filter.width": 0.8,
        "film.opencl.enable": False,
        "film.imagepipeline.0.type": "TONEMAP_LINEAR",
        "film.imagepipeline.0.scale": 1.0,
        "batch.halttime": 30,
        "batch.haltthreshold": 8 / 256,
        "batch.haltthreshold.warmup": 3,
        "batch.haltthreshold.step": 3,
        "batch.haltthreshold.filter.enable": False,
    }

    return utils.create_props(prefix, definitions)

def _get_preview_settings(depsgraph):
    objects = []
    active_mat = None

    for dg_obj_instance in depsgraph.object_instances:
        obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object

        if not obj.name == 'preview_hair' and not utils.is_instance_visible(dg_obj_instance, obj, None):
            continue

        if obj.name.startswith("preview"):
            active_mat = obj.active_material
            objects.append(obj)

    if objects:
        return PreviewType.MATERIAL, active_mat

    return PreviewType.NONE, None

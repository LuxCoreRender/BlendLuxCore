from mathutils import Matrix
import bpy
import math
import numpy as np
from .. import utils
from ..utils import node as utils_node
import pyluxcore
from .image import ImageExporter
from time import time
from ..utils.errorlog import LuxCoreErrorLog


def find_psys_modifier(obj, psys):
    for mod in obj.modifiers:
        if mod.type == "PARTICLE_SYSTEM" and mod.particle_system.name == psys.name:
            return mod
    return None


def convert_uvs(obj, psys, settings, uv_textures, engine, strands_count, start, dupli_count, mod, num_children):
    failure = np.empty(shape=0, dtype=np.float32)

    if settings.use_active_uv_map or settings.uv_map_name not in obj.data.uv_layers:
        active_uv = utils.find_active_uv(uv_textures)
        if active_uv:
            uv_index = uv_textures.find(active_uv.name)
        else:
            uv_index = -1
    else:
        uv_index = uv_textures.find(settings.uv_map_name)

    if uv_index == -1 or not uv_textures[uv_index].data:
        return failure

    if engine:
        engine.update_stats("Exporting...", "[%s: %s] Preparing %d UV coordinates"
                             % (obj.name, psys.name, strands_count))

    first_particle = psys.particles[0]
    f = psys.uv_on_emitter
    uvs = np.fromiter((elem
                       for i in range(start, dupli_count)
                       for elem in f(mod, particle=psys.particles[i] if num_children == 0 else first_particle,
                                     particle_no=i, uv_no=uv_index)),
                      dtype=np.float32,
                      count=(dupli_count - start) * 2)
    return uvs

def convert_colors(obj, psys, settings, vertex_colors, engine, strands_count, start, dupli_count, mod, num_children):
    failure = np.empty(shape=0, dtype=np.float32)

    if settings.use_active_vertex_color_layer or settings.vertex_color_layer_name not in vertex_colors:
        active_vertex_color_layer = utils.find_active_vertex_color_layer(vertex_colors)
        if active_vertex_color_layer:
            vertex_color_index = vertex_colors.find(active_vertex_color_layer.name)
        else:
            vertex_color_index = -1
    else:
        vertex_color_index = vertex_colors.find(settings.vertex_color_layer_name)

    if vertex_color_index == -1 or not vertex_colors[vertex_color_index].data:
        return failure

    if engine:
        engine.update_stats("Exporting...", "[%s: %s] Preparing %d vertex colors"
                            % (obj.name, psys.name, strands_count))

    first_particle = psys.particles[0]
    f = psys.mcol_on_emitter
    colors = np.fromiter((elem
                          for i in range(start, dupli_count)
                          for elem in f(mod, psys.particles[i] if num_children == 0 else first_particle,
                                        particle_no= i, vcol_no=vertex_color_index)),
                         dtype=np.float32,
                         count=(dupli_count - start) * 3)
    return colors


def warn_about_missing_uvs(obj, node_tree):
    # TODO once we have a triplanar option for imagemaps, ignore imagemaps with
    #  triplanar in this check because they have no problems with missing UVs
    has_imagemaps = utils_node.has_nodes(node_tree, "LuxCoreNodeTexImagemap", True)
    if has_imagemaps and not utils_node.has_valid_uv_map(obj):
        msg = ("Image textures used, but no UVs defined. "
               "In case of bumpmaps this can lead to artifacts")
        LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)


def convert_hair(exporter, obj, obj_key, psys, depsgraph, luxcore_scene, scene_props, is_viewport_render,
                 is_for_duplication, instance_matrix_world, visible_to_camera, engine=None):
    try:
        assert psys.settings.render_type == "PATH"
        scene = depsgraph.scene_eval
        start_time = time()

        mod = find_psys_modifier(obj, psys)

        msg = "[%s: %s] Exporting hair" % (obj.name, psys.name)
        print(msg)
        if engine:
            engine.update_stats('Exporting...', msg)

        settings = psys.settings.luxcore.hair
        strand_diameter = settings.hair_size
        root_width = settings.root_width / 100
        tip_width = settings.tip_width / 100
        width_offset = settings.width_offset / 100

        if not is_viewport_render:
            steps = 2 ** psys.settings.render_step
        else:
            steps = 2 ** psys.settings.display_step
        points_per_strand = steps + 1

        num_parents = len(psys.particles)
        num_children = len(psys.child_particles)
        dupli_count = num_parents + num_children

        if num_children == 0:
            start = 0
        else:
            # Number of virtual parents reduces the number of exported children
            num_virtual_parents = math.trunc(
                0.3 * psys.settings.virtual_parents * len(psys.child_particles) * num_parents)
            start = num_parents + num_virtual_parents

        # Collect point/color/uv information from Blender
        # (unfortunately this can't be accelerated in C++)
        collection_start = time()
        strands_count = dupli_count - start

        # Point coordinates as a flattened numpy array
        point_count = strands_count * points_per_strand
        if engine:
            engine.update_stats("Exporting...", "[%s: %s] Preparing %d points"
                                % (obj.name, psys.name, point_count))
        co_hair = psys.co_hair
        points = np.fromiter((elem
                              for pindex in range(start, dupli_count)
                              for step in range(points_per_strand)
                              for elem in co_hair(object=obj, particle_no=pindex, step=step)),
                             dtype=np.float32,
                             count=point_count * 3)

        colors = np.empty(shape=0, dtype=np.float32)
        uvs = np.empty(shape=0, dtype=np.float32)
        image_filename = ""
        uvs_needed = settings.copy_uv_coords
        copy_uvs = settings.copy_uv_coords

        if settings.export_color != "none" or uvs_needed:
            emitter_mesh = obj.to_mesh(depsgraph=depsgraph)
            uv_textures = emitter_mesh.uv_layers
            vertex_colors = emitter_mesh.vertex_colors

            if settings.export_color == "uv_texture_map" and settings.image:
                try:
                    image_filename = ImageExporter.export(settings.image, settings.image_user, scene)
                    uvs_needed = True
                except OSError as error:
                    msg = "%s (Object: %s, Particle System: %s)" % (error, obj.name, psys.name)
                    LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
            elif settings.export_color == "vertex_color":
                colors = convert_colors(obj, psys, settings, vertex_colors, engine,
                                        strands_count, start, dupli_count, mod, num_children)

            if uvs_needed:
                uvs = convert_uvs(obj, psys, settings, uv_textures, engine,
                                  strands_count, start, dupli_count, mod, num_children)

            obj.to_mesh_clear()

        if len(uvs) == 0:
            copy_uvs = False

        print("Collecting Blender hair information took %.3f s" % (time() - collection_start))
        if engine:
            engine.update_stats("Exporting...", "Refining Hair System %s" % psys.name)
            if engine.test_break():
                return None

        lux_shape_name = make_hair_shape_name(obj_key, psys)

        if is_for_duplication:
            # We have to unapply the transformation which is baked into the Blender hair coordinates
            transformation = utils.matrix_to_list(obj.matrix_world, invert=True)
        else:
            transformation = None

        success = luxcore_scene.DefineBlenderStrands(lux_shape_name, points_per_strand,
                                                     points, colors, uvs, image_filename, settings.gamma,
                                                     copy_uvs, transformation, strand_diameter,
                                                     root_width, tip_width, width_offset,
                                                     settings.tesseltype, settings.adaptive_maxdepth,
                                                     settings.adaptive_error, settings.solid_sidecount,
                                                     settings.solid_capbottom, settings.solid_captop,
                                                     list(settings.root_color), list(settings.tip_color))

        # Sometimes no hair shape could be created, e.g. if the length
        # of all hairs is 0 (can happen e.g. during animations or if hair length is textured)
        if not success:
            return None

        time_elapsed = time() - start_time
        if exporter.stats:
            exporter.stats.export_time_hair.value += time_elapsed
        print("[%s: %s] Hair export finished (%.3f s)" % (obj.name, psys.name, time_elapsed))
        return lux_shape_name
    except Exception as error:
        msg = "[%s: %s] %s" % (obj.name, psys.name, error)
        LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
        if str(error).strip() != "Error: Object was not yet evaluated":
            import traceback
            traceback.print_exc()
        return None


def set_hair_props(scene_props, lux_obj, lux_shape, lux_mat, visible_to_camera,
                   is_for_duplication, instance_matrix_world, use_instancing):
    prefix = "scene.objects." + lux_obj + "."

    scene_props.Set(pyluxcore.Property(prefix + "material", lux_mat))
    scene_props.Set(pyluxcore.Property(prefix + "shape", lux_shape))
    scene_props.Set(pyluxcore.Property(prefix + "camerainvisible", not visible_to_camera))

    if is_for_duplication:
        scene_props.Set(pyluxcore.Property(prefix + "transformation", utils.matrix_to_list(instance_matrix_world)))
    elif use_instancing:
        # We don't actually need to transform anything, just set an identity matrix so the mesh is instanced
        identity_matrix = utils.matrix_to_list(Matrix.Identity(4))
        scene_props.Set(pyluxcore.Property(prefix + "transformation", identity_matrix))


def make_hair_shape_name(obj_key, psys):
    # Can't use the memory address of the psys as key because it changes
    # when the psys is updated (e.g. because some hair moves)
    return obj_key + "_" + utils.sanitize_luxcore_name(psys.name)


def get_hair_material_index(psys):
    # For some reason this index is not starting at 0 but at 1 (Blender is strange)
    return psys.settings.material - 1


def get_strand_seg(idx, strand):
    if idx >= len(strand.points):
        return [0.0, 0.0, 0.0]
    else:
        return strand.points[idx].position

# Code for Hair Curves in Blender 3.5
def convert_hair_curves(exporter, depsgraph, obj, obj_key, luxcore_scene, is_for_duplication):
    start_time = time()
    lux_shape_name = obj_key
    time_elapsed = time() - start_time
    scene = depsgraph.scene_eval

    strands = obj.data.curves

    points_per_strand = np.fromiter((strand.points_length
                  for strand in strands), dtype=np.int32)

    points = np.fromiter((elem
                  for strand in strands
                  for idx in range(strand.points_length)
                  for elem in strand.points[idx].position), dtype=np.float32)

    colors = np.empty(shape=0, dtype=np.float32)
    uvs = np.empty(shape=0, dtype=np.float32)
    settings = obj.luxcore.hair

    strand_diameter = settings.hair_size
    root_width = settings.root_width / 100
    tip_width = settings.tip_width / 100
    width_offset = settings.width_offset / 100

    export_color = settings.export_color
    image = settings.image
    image_filename = ''
    uvs_needed = settings.copy_uv_coords
    copy_uvs = settings.copy_uv_coords

    if export_color != "none" or uvs_needed:
        emitter_mesh = obj.parent.to_mesh(depsgraph=depsgraph)
        vertex_colors = emitter_mesh.vertex_colors

        if export_color == "uv_texture_map" and image:
            try:
                image_filename = ImageExporter.export(image, settings.image_user, scene)
                uvs_needed = True
            except OSError as error:
                msg = "%s (Object: %s, Hair Curves: %s)" % (error, obj.name, obj.data.name)
                LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
    #     elif settings.export_color == "vertex_color":
    #         colors = convert_colors(obj, psys, settings, vertex_colors, engine,
    #                                 strands_count, start, dupli_count, mod, num_children)

        if uvs_needed:
            uvs = np.fromiter((elem
                           for uv_coord in obj.data.attributes['surface_uv_coordinate'].data
                           for elem in uv_coord.vector),
                          dtype=np.float32)

    if len(uvs) == 0:
        copy_uvs = False

    transformation = None
    success = luxcore_scene.DefineBlenderCurveStrands(lux_shape_name, points_per_strand,
                                                 points, colors, uvs, image_filename, settings.gamma,
                                                 copy_uvs, transformation, strand_diameter,
                                                 root_width, tip_width, width_offset,
                                                 settings.tesseltype, settings.adaptive_maxdepth,
                                                 settings.adaptive_error, settings.solid_sidecount,
                                                 settings.solid_capbottom, settings.solid_captop,
                                                 list(settings.root_color), list(settings.tip_color))

    if not success:
        return None

    if exporter.stats:
        exporter.stats.export_time_hair.value += time_elapsed
    return lux_shape_name
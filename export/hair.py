import bpy
from ..bin import pyluxcore
from .image import ImageExporter
from . import material
from .. import utils
from time import time
import math
import numpy as np


def find_psys_modifier(obj, psys):
    for mod in obj.modifiers:
        if mod.type == "PARTICLE_SYSTEM" and mod.particle_system.name == psys.name:
            return mod
    return None


def is_psys_visible(obj, psys_modifier, scene, context):
    if psys_modifier is None:
        return False

    if not utils.is_obj_visible(obj, scene, context):
        # Emitter is not on a visible layer
        return False

    visible = (context and psys_modifier.show_viewport) or (not context and psys_modifier.show_render)
    return visible


def restore_resolution(scene, obj, psys, final_render):
    if final_render:
        # Resolution was changed to "RENDER" for final renders, change it back
        psys.set_resolution(scene, obj, "PREVIEW")


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
                       for elem in f(mod, psys.particles[i] if num_children == 0 else first_particle,
                                     i, uv_index)),
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
                          for elem in f(mod, psys.particles[i - start] if num_children == 0 else first_particle,
                                        i - start, vertex_color_index)),
                         dtype=np.float32,
                         count=(dupli_count - start) * 3)
    return colors


def convert_hair(exporter, obj, psys, luxcore_scene, scene, context=None, engine=None):
    try:
        assert psys.settings.render_type == "PATH"
        start_time = time()

        mod = find_psys_modifier(obj, psys)
        if not is_psys_visible(obj, mod, scene, context):
            return

        msg = "[%s: %s] Exporting hair" % (obj.name, psys.name)
        print(msg)
        if engine:
            engine.update_stats('Exporting...', msg)

        final_render = not context
        worldscale = utils.get_worldscale(scene, as_scalematrix=False)

        settings = psys.settings.luxcore.hair
        strand_diameter = settings.hair_size * worldscale
        root_width = settings.root_width / 100
        tip_width = settings.tip_width / 100
        width_offset = settings.width_offset / 100

        if final_render:
            set_res_start = time()
            psys.set_resolution(scene, obj, "RENDER")
            print("Changing resolution to RENDER took %.3f s" % (time() - set_res_start))
            if engine and engine.test_break():
                restore_resolution(scene, obj, psys, final_render)
                return

            steps = 2 ** psys.settings.render_step
        else:
            steps = 2 ** psys.settings.draw_step
        points_per_strand = steps + 1

        num_parents = len(psys.particles)
        num_children = len(psys.child_particles)
        dupli_count = num_parents + num_children

        if num_children == 0:
            start = 0
        else:
            # Number of virtual parents reduces the number of exported children
            num_virtual_parents = math.trunc(0.3 * psys.settings.virtual_parents
                                             * psys.settings.child_nbr * num_parents)
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
                              for elem in co_hair(obj, pindex, step)),
                             dtype=np.float32,
                             count=point_count * 3)

        colors = np.empty(shape=0, dtype=np.float32)
        uvs = np.empty(shape=0, dtype=np.float32)
        image_filename = ""
        uvs_needed = settings.copy_uv_coords
        copy_uvs = settings.copy_uv_coords

        if settings.export_color != "none" or uvs_needed:
            modifier_mode = "RENDER" if final_render else "PREVIEW"
            emitter_mesh = obj.to_mesh(scene, True, modifier_mode)
            uv_textures = emitter_mesh.tessface_uv_textures
            vertex_colors = emitter_mesh.tessface_vertex_colors

            if settings.export_color == "uv_texture_map" and settings.image:
                try:
                    image_filename = ImageExporter.export(settings.image, settings.image_user, scene)
                    uvs_needed = True
                except OSError as error:
                    msg = "%s (Object: %s, Particle System: %s)" % (error, obj.name, psys.name)
                    scene.luxcore.errorlog.add_warning(msg, obj_name=obj.name)
            elif settings.export_color == "vertex_color":
                colors = convert_colors(obj, psys, settings, vertex_colors, engine,
                                        strands_count, start, dupli_count, mod, num_children)

            if uvs_needed:
                uvs = convert_uvs(obj, psys, settings, uv_textures, engine,
                                  strands_count, start, dupli_count, mod, num_children)

            bpy.data.meshes.remove(emitter_mesh, do_unlink=False)

        if len(uvs) == 0:
            copy_uvs = False

        restore_resolution(scene, obj, psys, final_render)
        print("Collecting Blender hair information took %.3f s" % (time() - collection_start))
        if engine and engine.test_break():
            return

        luxcore_shape_name = utils.get_luxcore_name(obj, context) + "_" + utils.get_luxcore_name(psys)
        if engine:
            engine.update_stats("Exporting...", "Refining Hair System %s" % psys.name)
        success = luxcore_scene.DefineBlenderStrands(luxcore_shape_name, points_per_strand,
                                                     points, colors, uvs, image_filename, settings.gamma,
                                                     copy_uvs, worldscale, strand_diameter,
                                                     root_width, tip_width, width_offset,
                                                     settings.tesseltype, settings.adaptive_maxdepth,
                                                     settings.adaptive_error, settings.solid_sidecount,
                                                     settings.solid_capbottom, settings.solid_captop,
                                                     list(settings.root_color), list(settings.tip_color))

        # Sometimes no hair shape could be created, e.g. if the length
        # of all hairs is 0 (can happen e.g. during animations or if hair length is textured)
        if success:
            # For some reason this index is not starting at 0 but at 1 (Blender is strange)
            material_index = psys.settings.material - 1

            render_layer = utils.get_current_render_layer(scene)
            override_mat = render_layer.material_override if render_layer else None

            if not context and override_mat:
                # Only use override material in final render
                mat = override_mat
            else:
                try:
                    mat = obj.material_slots[material_index].material
                except IndexError:
                    mat = None
                    print('WARNING: material slot %d on object "%s" is unassigned!' % (material_index + 1, obj.name))

            strandsProps = pyluxcore.Properties()

            lux_mat_name, mat_props = material.convert(exporter, mat, scene, context, obj.name)
            strandsProps.Set(mat_props)

            prefix = "scene.objects." + luxcore_shape_name + "."

            strandsProps.Set(pyluxcore.Property(prefix + "material", lux_mat_name))
            strandsProps.Set(pyluxcore.Property(prefix + "shape", luxcore_shape_name))
            if settings.instancing == "enabled":
                # We don't actually need to transform anything, just set an identity matrix so the mesh is instanced
                from mathutils import Matrix
                transform = utils.matrix_to_list(Matrix.Identity(4))
                strandsProps.Set(pyluxcore.Property(prefix + "transformation", transform))

            visible_to_cam = utils.is_obj_visible_to_cam(obj, scene, context)
            strandsProps.Set(pyluxcore.Property(prefix + "camerainvisible", not visible_to_cam))

            luxcore_scene.Parse(strandsProps)

        time_elapsed = time() - start_time
        print("[%s: %s] Hair export finished (%.3f s)" % (obj.name, psys.name, time_elapsed))
    except Exception as error:
        msg = "[%s: %s] %s" % (obj.name, psys.name, error)
        scene.luxcore.errorlog.add_warning(msg, obj_name=obj.name)
        import traceback
        traceback.print_exc()

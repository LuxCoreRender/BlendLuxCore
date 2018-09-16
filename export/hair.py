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


def convert_uvs(obj, psys, scene, settings, uv_textures, engine, strands_count, start, dupli_count, mod, num_children):
    failure = np.empty(shape=0, dtype=np.float32), ""
    image_filename = ""

    try:
        image_filename = ImageExporter.export(settings.image, settings.image_user, scene)
    except OSError as error:
        msg = "%s (Object: %s, Particle System: %s)" % (error, obj.name, psys.name)
        scene.luxcore.errorlog.add_warning(msg)

    # If the image was invalid/not found, we should not collect UV data
    if not image_filename:
        return failure

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
                       for elem in f(mod, psys.particles[i - start] if num_children == 0 else first_particle,
                                     i - start, uv_index)),
                      dtype=np.float32,
                      count=(dupli_count - start) * 2)
    return uvs, image_filename


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
    # convert_hair_old(exporter, obj, psys, luxcore_scene, scene, context, engine)
    convert_hair_new(exporter, obj, psys, luxcore_scene, scene, context, engine)


def convert_hair_new(exporter, obj, psys, luxcore_scene, scene, context=None, engine=None):
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

        ##########
        # Stuff I need to collect from Blender:
        # - co = psys.co_hair(obj, pindex, step)
        # - uv_co = psys.uv_on_emitter(mod, psys.particles[i], pindex, uv_textures.active_index)
        # - col = psys.mcol_on_emitter(mod, psys.particles[i], pindex, vertex_color.active_index)

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

        if settings.export_color != "none":
            modifier_mode = "RENDER" if final_render else "PREVIEW"
            emitter_mesh = obj.to_mesh(scene, True, modifier_mode)
            uv_textures = emitter_mesh.tessface_uv_textures
            vertex_colors = emitter_mesh.tessface_vertex_colors

            if settings.export_color == "uv_texture_map":
                uvs, image_filename = convert_uvs(obj, psys, scene, settings, uv_textures, engine,
                                                  strands_count, start, dupli_count, mod, num_children)

            elif settings.export_color == "vertex_color":
                colors = convert_colors(obj, psys, settings, vertex_colors, engine,
                                        strands_count, start, dupli_count, mod, num_children)

            bpy.data.meshes.remove(emitter_mesh, do_unlink=False)

        restore_resolution(scene, obj, psys, final_render)
        print("Collecting Blender hair information took %.3f s" % (time() - collection_start))
        if engine and engine.test_break():
            return

        luxcore_shape_name = utils.get_luxcore_name(obj, context) + "_" + utils.get_luxcore_name(psys)
        if engine:
            engine.update_stats("Exporting...", "Refining Hair System %s" % psys.name)
        success = luxcore_scene.DefineBlenderStrands(luxcore_shape_name, points_per_strand,
                                                     points, colors, uvs, image_filename,
                                                     worldscale, strand_diameter, root_width,
                                                     tip_width, width_offset,
                                                     settings.tesseltype, settings.adaptive_maxdepth,
                                                     settings.adaptive_error, settings.solid_sidecount,
                                                     settings.solid_capbottom, settings.solid_captop)

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

            lux_mat_name, mat_props = material.convert(exporter, mat, scene, context)
            strandsProps.Set(mat_props)

            prefix = "scene.objects." + luxcore_shape_name + "."

            strandsProps.Set(pyluxcore.Property(prefix + "material", lux_mat_name))
            strandsProps.Set(pyluxcore.Property(prefix + "shape", luxcore_shape_name))

            visible_to_cam = utils.is_obj_visible_to_cam(obj, scene, context)
            strandsProps.Set(pyluxcore.Property(prefix + "camerainvisible", not visible_to_cam))

            luxcore_scene.Parse(strandsProps)

        time_elapsed = time() - start_time
        print("[%s: %s] New Hair export finished (%.3f s)" % (obj.name, psys.name, time_elapsed))
    except Exception as error:
        msg = "[%s: %s] %s" % (obj.name, psys.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()


def convert_hair_old(exporter, obj, psys, luxcore_scene, scene, context=None, engine=None):
    try:
        assert psys.settings.render_type == "PATH"

        if not obj.modifiers:
            return

        for mod in obj.modifiers:
            if mod.type == "PARTICLE_SYSTEM":
                if mod.particle_system.name == psys.name:
                    break

        if not mod.type == "PARTICLE_SYSTEM":
            return
        elif not mod.particle_system.name == psys.name:
            return

        if not utils.is_obj_visible(obj, scene, context):
            # Emitter is not on a visible layer
            return

        visible = (context and mod.show_viewport) or (not context and mod.show_render)
        if not visible:
            return

        print("[%s: %s] Exporting hair" % (obj.name, psys.name))
        start_time = time()

        settings = psys.settings.luxcore.hair

        hair_size = settings.hair_size
        root_width = settings.root_width / 100
        tip_width = settings.tip_width / 100
        width_offset = settings.width_offset / 100

        steps = 2 ** psys.settings.draw_step

        if not context:
            psys.set_resolution(scene, obj, "RENDER")
            steps = 2 ** psys.settings.render_step

        num_parents = len(psys.particles)
        num_children = len(psys.child_particles)

        if num_children == 0:
            start = 0
        else:
            # Number of virtual parents reduces the number of exported children
            num_virtual_parents = math.trunc(
                0.3 * psys.settings.virtual_parents * psys.settings.child_nbr * num_parents)
            start = num_parents + num_virtual_parents

        segments = []
        points = []
        thickness = []
        colors = []
        uv_coords = []
        total_segments_count = 0
        has_vertex_colors = False
        colorflag = False
        uvflag = False
        image_width = 0
        image_height = 0
        image_pixels = []
        image_valid = False

        if settings.export_color != "none":
            modifier_mode = "PREVIEW" if context else "RENDER"
            mesh = obj.to_mesh(scene, True, modifier_mode)
            uv_textures = mesh.tessface_uv_textures
            vertex_color = mesh.tessface_vertex_colors

            has_vertex_colors = vertex_color.active and vertex_color.active.data
            has_uv_texture = uv_textures.active and uv_textures.active.data

            if settings.export_color == "vertex_color" and has_vertex_colors:
                colorflag = True

            if settings.export_color == "uv_texture_map":
                if has_uv_texture:
                    uv_tex = uv_textures.active.data
                    image = uv_tex[0].image
                    if image:
                        image_width = image.size[0]
                        image_height = image.size[1]
                        image_pixels = image.pixels[:]
                        image_valid = len(image_pixels)
                        colorflag = True
                    uvflag = True

        transform = obj.matrix_world.inverted()
        total_strand_count = 0

        if root_width == tip_width:
            thicknessflag = 0
            hair_size *= root_width
        else:
            thicknessflag = 1

        dupli_count = num_parents + num_children
        i = 0

        for pindex in range(start, dupli_count):
            if num_children == 0:
                i = pindex

            # Make it possible to interrupt the export process
            if engine and pindex % 1000 == 0:
                progress = (pindex / dupli_count) * 100
                engine.update_stats("Export", "Object: %s (Hair Particles: %d%%)" % (obj.name, progress))

                if engine.test_break():
                    return

            # A small optimization in order to speedup the export
            # process: cache the uv_co and color value
            uv_co = None
            col = None
            seg_length = 1.0
            point_count = 0

            for step in range(0, steps+1):
                co = psys.co_hair(obj, pindex, step)
                # type(co) is Vector (with 3 elements)

                if step > 0 and points:
                    seg_length = (co - obj.matrix_world * points[-1]).length_squared

                if not (co.length_squared == 0 or seg_length == 0):
                    points.append(transform * co)

                    if thicknessflag:
                        if step > steps * width_offset:
                            thick = (root_width * (steps - step - 1) + tip_width * (
                                        step - steps * width_offset)) / (
                                        steps * (1 - width_offset) - 1)
                        else:
                            thick = root_width

                        thickness.append(thick * hair_size)

                    point_count += 1

                    if settings.export_color == "uv_texture_map" and image_valid:
                        if uvflag:
                            if not uv_co:
                                uv_co = psys.uv_on_emitter(mod, psys.particles[i], pindex, uv_textures.active_index)
                                # print("uv_co:", type(uv_co))
                                # type(uv_co) is Vector (with 2 elements)

                            uv_coords.append(uv_co)
                        if not col:
                            x_co = round(uv_co[0] * (image_width - 1))
                            y_co = round(uv_co[1] * (image_height - 1))

                            pixelnumber = (image_width * y_co) + x_co

                            r = image_pixels[pixelnumber * 4]
                            g = image_pixels[pixelnumber * 4 + 1]
                            b = image_pixels[pixelnumber * 4 + 2]
                            col = (r, g, b)

                        colors.append(col)
                    elif settings.export_color == "vertex_color" and has_vertex_colors:
                        if not col:
                            col = psys.mcol_on_emitter(mod, psys.particles[i], pindex, vertex_color.active_index)
                            # print("col:", type(col))
                            # type(col) is "tuple" (with 3 elements)

                        colors.append(col)

            if point_count == 1:
                points.pop()

                if thicknessflag:
                    thickness.pop()
                point_count -= 1
            elif point_count > 1:
                segments.append(point_count - 1)
                total_strand_count += 1
                total_segments_count = total_segments_count + point_count - 1

        if settings.export_color != "none":
            # Delete the temporary mesh we had to create
            bpy.data.meshes.remove(mesh, do_unlink=False)

        # LuxCore needs tuples, not vectors
        points_as_tuples = [tuple(point) for point in points]

        if not thicknessflag:
            thickness = hair_size

        if not colorflag:
            colors = (1.0, 1.0, 1.0)

        if not uvflag:
            uvs_as_tuples = None
        else:
            # LuxCore needs tuples, not vectors
            uvs_as_tuples = [tuple(uv) for uv in uv_coords]

        luxcore_shape_name = utils.get_luxcore_name(obj, context) + "_" + utils.get_luxcore_name(psys)

        if engine:
            engine.update_stats("Exporting...", "Refining Hair System %s" % psys.name)
        # Documentation: http://www.luxrender.net/forum/viewtopic.php?f=8&t=12116&sid=03a16c5c345db3ee0f8126f28f1063c8#p112819

        luxcore_scene.DefineStrands(luxcore_shape_name, total_strand_count, len(points), points_as_tuples, segments,
                                    thickness, 0.0, colors, uvs_as_tuples,
                                    settings.tesseltype, settings.adaptive_maxdepth, settings.adaptive_error,
                                    settings.solid_sidecount, settings.solid_capbottom, settings.solid_captop, True)

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

        # Convert material
        strandsProps = pyluxcore.Properties()

        lux_mat_name, mat_props = material.convert(exporter, mat, scene, context)
        strandsProps.Set(mat_props)

        # The hair shape is located at world origin and implicitly instanced, so we have to
        # move it to the correct position
        transform = utils.matrix_to_list(obj.matrix_world, scene, apply_worldscale=True)

        prefix = "scene.objects." + luxcore_shape_name + "."

        strandsProps.Set(pyluxcore.Property(prefix + "material", lux_mat_name))
        strandsProps.Set(pyluxcore.Property(prefix + "shape", luxcore_shape_name))
        strandsProps.Set(pyluxcore.Property(prefix + "transformation", transform))

        visible_to_cam = utils.is_obj_visible_to_cam(obj, scene, context)
        strandsProps.Set(pyluxcore.Property(prefix + "camerainvisible", not visible_to_cam))

        luxcore_scene.Parse(strandsProps)

        if not context:
            # Resolution was changed to "RENDER" for final renders, change it back
            psys.set_resolution(scene, obj, "PREVIEW")

        time_elapsed = time() - start_time
        print("[%s: %s] Hair export finished (%.3f s)" % (obj.name, psys.name, time_elapsed))
    except Exception as error:
        msg = "[%s: %s] %s" % (obj.name, psys.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()

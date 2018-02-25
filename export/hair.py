from ..bin import pyluxcore
from . import material
from .. import utils
from time import time
import math

def convert_hair(blender_obj, psys, luxcore_scene, scene, context=None, engine=None):
    try:
        assert psys.settings.render_type == "PATH"

        if not blender_obj.modifiers:
            return

        for mod in blender_obj.modifiers:
            if mod.type == "PARTICLE_SYSTEM":
                if mod.particle_system.name == psys.name:
                    break

        if not mod.type == "PARTICLE_SYSTEM":
            return
        elif not mod.particle_system.name == psys.name:
            return

        if not utils.is_obj_visible(blender_obj, scene, context):
            # Emitter is not on a visible layer
            return

        visible = (context and mod.show_viewport) or (not context and mod.show_render)
        if not visible:
            return

        print("[%s: %s] Exporting hair" % (blender_obj.name, psys.name))
        start_time = time()

        settings = psys.settings.luxcore.hair

        hair_size = settings.hair_size
        root_width = settings.root_width
        tip_width = settings.tip_width
        width_offset = settings.width_offset

        steps = 2 ** psys.settings.draw_step

        if not context:
            psys.set_resolution(scene, blender_obj, "RENDER")
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
        uv_tex = None
        colorflag = False
        uvflag = False
        thicknessflag = 0
        image_width = 0
        image_height = 0
        image_pixels = []

        modifier_mode = "PREVIEW" if context else "RENDER"
        mesh = blender_obj.to_mesh(scene, True, modifier_mode)
        uv_textures = mesh.tessface_uv_textures
        vertex_color = mesh.tessface_vertex_colors

        has_vertex_colors = True if (vertex_color.active and vertex_color.active.data) else False
        has_uv_texture =  True if (uv_textures.active and uv_textures.active.data) else False

        if settings.export_color == "vertex_color" and has_vertex_colors:
            colorflag = True

        if settings.export_color == "uv_texture_map":
            if has_uv_texture:
                uv_tex = uv_textures.active.data
                if uv_tex[0].image:
                    image_width = uv_tex[0].image.size[0]
                    image_height = uv_tex[0].image.size[1]
                    image_pixels = uv_tex[0].image.pixels[:]
                    colorflag = True
                uvflag = True

        transform = blender_obj.matrix_world.inverted()
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
                engine.update_stats("Export", "Object: %s (Hair Particles: %d%%)" % (blender_obj.name, progress))

                if engine.test_break():
                    return

            # A small optimization in order to speedup the export
            # process: cache the uv_co and color value
            uv_co = None
            col = None
            seg_length = 1.0
            point_count = 0

            for step in range(0, steps+1):
                co = psys.co_hair(blender_obj, pindex, step)
                if step > 0 and points:
                    seg_length = (co - blender_obj.matrix_world * points[-1]).length_squared

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

                    if settings.export_color == 'uv_texture_map' and not len(image_pixels) == 0:
                        if uvflag:
                            if not uv_co:
                                uv_co = psys.uv_on_emitter(mod, psys.particles[i], pindex, uv_textures.active_index)

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

        luxcore_shape_name = utils.get_luxcore_name(blender_obj, context) + "_" + utils.get_luxcore_name(psys)

        if engine:
            engine.update_stats('Exporting...', 'Refining Hair System %s' % psys.name)
        # Documentation: http://www.luxrender.net/forum/viewtopic.php?f=8&t=12116&sid=03a16c5c345db3ee0f8126f28f1063c8#p112819

        luxcore_scene.DefineStrands(luxcore_shape_name, total_strand_count, len(points), points_as_tuples, segments,
                                    thickness, 0.0, colors, uvs_as_tuples,
                                    settings.tesseltype, settings.adaptive_maxdepth, settings.adaptive_error,
                                    settings.solid_sidecount, settings.solid_capbottom, settings.solid_captop, True)

        # For some reason this index is not starting at 0 but at 1 (Blender is strange)
        material_index = psys.settings.material - 1

        current_render_layer = scene.render.layers[scene.luxcore.active_layer_index]
        override_mat = current_render_layer.material_override

        if not context and override_mat:
            # Only use override material in final render
            mat = override_mat
        else:
            try:
                mat = blender_obj.material_slots[material_index].material
            except IndexError:
                mat = None
                print('WARNING: material slot %d on object "%s" is unassigned!' % (material_index + 1, blender_obj.name))

        ## Convert material
        strandsProps = pyluxcore.Properties()

        lux_mat_name, mat_props = material.convert(mat, scene, context)
        strandsProps.Set(mat_props)

        # The hair shape is located at world origin and implicitly instanced, so we have to
        # move it to the correct position
        transform = utils.matrix_to_list(blender_obj.matrix_world, scene, apply_worldscale=True)

        prefix = "scene.objects." + luxcore_shape_name + "."

        strandsProps.Set(pyluxcore.Property(prefix + "material", lux_mat_name))
        strandsProps.Set(pyluxcore.Property(prefix + "shape", luxcore_shape_name))
        strandsProps.Set(pyluxcore.Property(prefix + "transformation", transform))

        visible_to_cam = utils.is_obj_visible_to_cam(blender_obj, scene, context)
        strandsProps.Set(pyluxcore.Property(prefix + "camerainvisible", not visible_to_cam))

        luxcore_scene.Parse(strandsProps)

        if not context:
            # Resolution was changed to "RENDER" for final renders, change it back
            psys.set_resolution(scene, blender_obj, "PREVIEW")

        time_elapsed = time() - start_time
        print("[%s: %s] Hair export finished (%.3fs)" % (blender_obj.name, psys.name, time_elapsed))
    except Exception as error:
        msg = "[%s: %s] %s" % (blender_obj.name, psys.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()

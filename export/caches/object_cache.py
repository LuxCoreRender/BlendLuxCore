import bpy
from ...bin import pyluxcore
from ... import utils
from .. import mesh_converter
from .exported_data import ExportedObject
from .. import light

MESH_OBJECTS = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
EXPORTABLE_OBJECTS = MESH_OBJECTS | {"LIGHT"}


def get_material(obj, material_index, exporter, depsgraph, is_viewport_render):
    from ...utils.errorlog import LuxCoreErrorLog
    from ...utils import node as utils_node
    from .. import material
    if material_index < len(obj.material_slots):
        mat = obj.material_slots[material_index].material

        if mat is None:
            # Note: material.convert returns the fallback material in this case
            msg = "No material attached to slot %d" % (material_index + 1)
            LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
    else:
        # The object has no material slots
        LuxCoreErrorLog.add_warning("No material defined", obj_name=obj.name)
        # Use fallback material
        mat = None

    if mat:
        if mat.luxcore.node_tree:
            imagemaps = utils_node.find_nodes(mat.luxcore.node_tree, "LuxCoreNodeTexImagemap")
            if imagemaps and not utils_node.has_valid_uv_map(obj):
                msg = (utils.pluralize("%d image texture", len(imagemaps)) + " used, but no UVs defined. "
                       "In case of bumpmaps this can lead to artifacts")
                LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)

        return material.convert(exporter, depsgraph, mat, is_viewport_render, obj.name)
    else:
        return material.fallback()

def find_psys_modifier(obj, psys):
    for mod in obj.modifiers:
        if mod.type == "PARTICLE_SYSTEM" and mod.particle_system.name == psys.name:
            return mod
    return None

class ObjectCache2:
    def __init__(self):
        self.exported_objects = {}
        self.exported_meshes = {}

    def first_run(self, exporter, depsgraph, view_layer, engine, luxcore_scene, scene_props, is_viewport_render):
        # TODO use luxcore_scene.DuplicateObjects for instances
        for index, dg_obj_instance in enumerate(depsgraph.object_instances, start=1):
            obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
            if not (self._is_visible(dg_obj_instance, obj) or obj.visible_get(view_layer=view_layer)):
                continue

            self._convert_obj(exporter, dg_obj_instance, obj, depsgraph,
                              luxcore_scene, scene_props, is_viewport_render)
            if engine:
                # Objects are the most expensive to export, so they dictate the progress
                # engine.update_progress(index / obj_amount)
                if engine.test_break():
                    return False

        self._debug_info()
        return True

    def _debug_info(self):
        print("Objects in cache:", len(self.exported_objects))
        print("Meshes in cache:", len(self.exported_meshes))
        for key, exported_mesh in self.exported_meshes.items():
            if exported_mesh:
                print(key, exported_mesh.mesh_definitions)
            else:
                print(key, "mesh is None")

    def _is_visible(self, dg_obj_instance, obj):
        return dg_obj_instance.show_self and obj.type in EXPORTABLE_OBJECTS

    def _get_mesh_key(self, obj, use_instancing, is_viewport_render=True):
        # Important: we need the data of the original object, not the evaluated one.
        # The instancing state has to be part of the key because a non-instanced mesh
        # has its transformation baked-in and can't be used by other instances.
        modified = utils.has_deforming_modifiers(obj.original)
        source = obj.original.data if (use_instancing and not modified) else obj.original
        key = utils.get_luxcore_name(source, is_viewport_render)
        if use_instancing:
            key += "_instance"
        return key

    def _convert_obj(self, exporter, dg_obj_instance, obj, depsgraph, luxcore_scene, scene_props, is_viewport_render):
        """ Convert one DepsgraphObjectInstance amd keep track of it """
        if obj.type == "EMPTY" or obj.data is None:
            return

        obj_key = utils.make_key_from_instance(dg_obj_instance)

        if obj.type in MESH_OBJECTS:
            if obj_key in self.exported_objects:
                raise Exception("key already in exp_obj:", obj_key)
            self._convert_mesh_obj(exporter, dg_obj_instance, obj, obj_key, depsgraph,
                                   luxcore_scene, scene_props, is_viewport_render)
        elif obj.type == "LIGHT":
            props, exported_stuff = light.convert_light(exporter, obj, obj_key, depsgraph, luxcore_scene,
                                                        dg_obj_instance.matrix_world.copy(), is_viewport_render)
            if exported_stuff:
                self.exported_objects[obj_key] = exported_stuff
                scene_props.Set(props)

        # Convert hair
        for psys in obj.particle_systems:
            settings = psys.settings

            if settings.type == "HAIR" and settings.render_type == "PATH":
                self._convert_hair(exporter, obj, psys, depsgraph, luxcore_scene, is_viewport_render)

    def _convert_mesh_obj(self, exporter, dg_obj_instance, obj, obj_key, depsgraph,
                          luxcore_scene, scene_props, is_viewport_render):
        transform = dg_obj_instance.matrix_world

        use_instancing = is_viewport_render or dg_obj_instance.is_instance or utils.can_share_mesh(obj.original)
        mesh_key = self._get_mesh_key(obj, use_instancing, is_viewport_render)
        # print(obj.name, "mesh key:", mesh_key)

        if use_instancing and mesh_key in self.exported_meshes:
            # print("retrieving mesh from cache")
            exported_mesh = self.exported_meshes[mesh_key]
        else:
            # print("fresh export")
            exported_mesh = mesh_converter.convert(obj, mesh_key, depsgraph, luxcore_scene,
                                                   is_viewport_render, use_instancing, transform)
            self.exported_meshes[mesh_key] = exported_mesh

        if exported_mesh:
            mat_names = []
            for shape_name, mat_index in exported_mesh.mesh_definitions:
                lux_mat_name, mat_props = get_material(obj, mat_index, exporter, depsgraph, is_viewport_render)
                scene_props.Set(mat_props)
                mat_names.append(lux_mat_name)

            obj_transform = transform.copy() if use_instancing else None
            exported_obj = ExportedObject(obj_key, exported_mesh.mesh_definitions, mat_names, obj_transform)
            if exported_obj:
                scene_props.Set(exported_obj.get_props())
                self.exported_objects[obj_key] = exported_obj

    def _convert_hair(self, exporter, obj, psys, depsgraph, luxcore_scene, is_viewport_render, engine=None):
        from time import time
        import math
        import numpy as np
        from ...utils.errorlog import LuxCoreErrorLog

        try:
            assert psys.settings.render_type == "PATH"
            scene = depsgraph.scene_eval
            start_time = time()

            # TODO 2.8 Do we have to check if emitter is on a visible layer
            # mod = find_psys_modifier(obj, psys)
            # if not is_psys_visible(obj, mod, scene, context):
            #    return

            msg = "[%s: %s] Exporting hair" % (obj.name, psys.name)
            print(msg)
            if engine:
                engine.update_stats('Exporting...', msg)

            worldscale = utils.get_worldscale(scene, as_scalematrix=False)

            settings = psys.settings.luxcore.hair
            strand_diameter = settings.hair_size * worldscale
            root_width = settings.root_width / 100
            tip_width = settings.tip_width / 100
            width_offset = settings.width_offset / 100

            if not is_viewport_render:
                # TODO 2.8 Check if we have to switch between render and viewport
                # set_res_start = time()
                # psys.set_resolution(scene, obj, "RENDER")
                # print("Changing resolution to RENDER took %.3f s" % (time() - set_res_start))
                # if engine and engine.test_break():
                #    restore_resolution(scene, obj, psys, final_render)
                #    return
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
                                  for elem in co_hair(object=obj, particle_no=pindex, step=step)),
                                 dtype=np.float32,
                                 count=point_count * 3)

            colors = np.empty(shape=0, dtype=np.float32)
            uvs = np.empty(shape=0, dtype=np.float32)
            image_filename = ""
            uvs_needed = settings.copy_uv_coords
            copy_uvs = settings.copy_uv_coords

            # TODO 2.8: adapt to_mesh to new API
            # if settings.export_color != "none" or uvs_needed:
            #     modifier_mode = "RENDER" if final_render else "PREVIEW"
            #     emitter_mesh = obj.to_mesh(scene, True, modifier_mode)
            #     uv_textures = emitter_mesh.tessface_uv_textures
            #     vertex_colors = emitter_mesh.tessface_vertex_colors
            #
            #     if settings.export_color == "uv_texture_map" and settings.image:
            #         try:
            #             image_filename = ImageExporter.export(settings.image, settings.image_user, scene)
            #             uvs_needed = True
            #         except OSError as error:
            #             msg = "%s (Object: %s, Particle System: %s)" % (error, obj.name, psys.name)
            #             LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
            #     elif settings.export_color == "vertex_color":
            #         colors = convert_colors(obj, psys, settings, vertex_colors, engine,
            #                                 strands_count, start, dupli_count, mod, num_children)
            #
            #     if uvs_needed:
            #         uvs = convert_uvs(obj, psys, settings, uv_textures, engine,
            #                           strands_count, start, dupli_count, mod, num_children)
            #
            #     bpy.data.meshes.remove(emitter_mesh, do_unlink=False)

            if len(uvs) == 0:
                copy_uvs = False

            # TODO 2.8 Check if we have to switch between render and viewport
            # restore_resolution(scene, obj, psys, final_render)
            print("Collecting Blender hair information took %.3f s" % (time() - collection_start))
            if engine and engine.test_break():
                return

            luxcore_shape_name = utils.get_luxcore_name(obj, is_viewport_render) + "_" + utils.get_luxcore_name(psys)

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
                lux_mat_name, mat_props = get_material(obj, psys.settings.material - 1, exporter, depsgraph, is_viewport_render)

                strandsProps = pyluxcore.Properties()
                strandsProps.Set(mat_props)
                prefix = "scene.objects." + luxcore_shape_name + "."

                strandsProps.Set(pyluxcore.Property(prefix + "material", lux_mat_name))
                strandsProps.Set(pyluxcore.Property(prefix + "shape", luxcore_shape_name))
                if settings.instancing == "enabled":
                    # We don't actually need to transform anything, just set an identity matrix so the mesh is instanced
                    from mathutils import Matrix
                    transform = utils.matrix_to_list(Matrix.Identity(4))
                    strandsProps.Set(pyluxcore.Property(prefix + "transformation", transform))

                #TODO 2.8 Adapt visibility checkt to new API
                # visible_to_cam = utils.is_obj_visible_to_cam(obj, scene, is_viewport_render)
                # strandsProps.Set(pyluxcore.Property(prefix + "camerainvisible", not visible_to_cam))

                luxcore_scene.Parse(strandsProps)

            time_elapsed = time() - start_time
            print("[%s: %s] Hair export finished (%.3f s)" % (obj.name, psys.name, time_elapsed))
        except Exception as error:
            msg = "[%s: %s] %s" % (obj.name, psys.name, error)
            LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
            import traceback
            traceback.print_exc()

    def diff(self, depsgraph):
        return depsgraph.id_type_updated("OBJECT")

    def update(self, exporter, depsgraph, luxcore_scene, scene_props, is_viewport_render=True):
        print("object cache update")

        # TODO maybe not loop over all instances, instead only loop over updated
        #  objects and check if they have a particle system that needs to be updated?
        #  Would be better for performance with many particles, however I'm not sure
        #  we can find all instances corresponding to one particle system?

        # For now, transforms and new instances only
        for dg_obj_instance in depsgraph.object_instances:
            obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
            if not self._is_visible(dg_obj_instance, obj):
                continue

            obj_key = utils.make_key_from_instance(dg_obj_instance)
            transform = dg_obj_instance.matrix_world.copy()

            if obj_key in self.exported_objects and obj.type != "LIGHT":
                exported_obj = self.exported_objects[obj_key]
                last_transform = exported_obj.transform
                if last_transform != transform:
                    # Update transform
                    exported_obj.transform = transform
                    scene_props.Set(exported_obj.get_props())
            else:
                # Object is new and not in LuxCore yet, or it is a light, do a full export
                # TODO use luxcore_scene.DuplicateObjects for instances
                self._convert_obj(exporter, dg_obj_instance, obj, depsgraph,
                                  luxcore_scene, scene_props, is_viewport_render)

        # Geometry updates (mesh edit, modifier edit etc.)
        if depsgraph.id_type_updated("OBJECT"):
            print("exported meshes:", self.exported_meshes.keys())

            for dg_update in depsgraph.updates:
                print(f"update id: {dg_update.id}, geom: {dg_update.is_updated_geometry}, trans: {dg_update.is_updated_transform}")

                if dg_update.is_updated_geometry and isinstance(dg_update.id, bpy.types.Object):
                    obj = dg_update.id
                    obj_key = utils.make_key(obj)

                    if obj.type in MESH_OBJECTS:
                        print(f"Geometry of obj {obj.name} was updated")
                        use_instancing = True
                        mesh_key = self._get_mesh_key(obj, use_instancing)
                        if mesh_key not in self.exported_meshes:
                            # Debug
                            raise Exception("NO MESH KEY FOUND")
                        transform = None  # In viewport render, everything is instanced
                        exported_mesh = mesh_converter.convert(obj, mesh_key, depsgraph, luxcore_scene,
                                                               is_viewport_render, use_instancing, transform)
                        self.exported_meshes[mesh_key] = exported_mesh
                        print(self.exported_meshes[mesh_key].mesh_definitions)
                    elif obj.type == "LIGHT":
                        print(f"Light obj {obj.name} was updated")
                        props, exported_stuff = light.convert_light(exporter, obj, obj_key, depsgraph, luxcore_scene,
                                                                    obj.matrix_world.copy(), is_viewport_render)
                        if exported_stuff:
                            self.exported_objects[obj_key] = exported_stuff
                            scene_props.Set(props)

        self._debug_info()

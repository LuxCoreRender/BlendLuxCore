import bpy
from array import array
from functools import lru_cache
from time import time

from ... import utils
import pyluxcore
from .. import mesh_converter
from ..hair import (
    convert_hair, warn_about_missing_uvs, set_hair_props, 
    make_hair_shape_name, get_hair_material_index,convert_hair_curves,
)
from .exported_data import ExportedObject, ExportedPart
from .. import light, material
from ...utils.errorlog import LuxCoreErrorLog
from ...utils import node as utils_node
from ...utils import MESH_OBJECTS
from ...utils.node import get_active_output

class TriAOVDataIndices:
    RANDOM_PER_ISLAND_INT = 0
    RANDOM_PER_ISLAND_FLOAT = 1


MAX_PARTICLES_FOR_LIVE_TRANSFORM = 2000


def uses_pointiness(node_tree):
    # TODO better check would be if the node is linked to the output and actually used
    return utils_node.has_nodes(node_tree, "LuxCoreNodeTexPointiness", True)


def uses_random_per_island_uniform_float(node_tree):
    # TODO better check would be if the node is linked to the output and actually used
    return utils_node.has_nodes(node_tree, "LuxCoreNodeTexRandomPerIsland", True)


def uses_random_per_island_int(node_tree):
    # TODO better check would be if the node is linked to the output and actually used
    for node in utils_node.find_nodes_multi(node_tree, {"LuxCoreNodeTexMapping2D", "LuxCoreNodeTexMapping3D"}, True):
        if node.mapping_type in {"uvrandommapping2d", "localrandommapping3d"} and node.seed_type == "mesh_islands":
            return True
    return False


def needs_edge_detector_shape(node_tree):
    # TODO better check would be if the node is linked to the output and actually used
    for node in utils_node.find_nodes(node_tree, "LuxCoreNodeTexWireframe", True):
        if node.hide_planar_edges:
            return True
    return False


def uses_displacement(obj):
    for mat_slot in obj.material_slots:
        mat = mat_slot.material
        if (mat and mat.luxcore.node_tree
                and utils_node.has_nodes_multi(mat.luxcore.node_tree, {"LuxCoreNodeShapeHeightDisplacement",
                                                                       "LuxCoreNodeShapeVectorDisplacement"}, True)):
            return True
    return False

def define_shapes(input_shape, node_tree, exporter, depsgraph, scene_props):
    shape = input_shape

    output_node = get_active_output(node_tree)
    if output_node:
        # Convert the whole shape stack
        shape = output_node.inputs["Shape"].export_shape(exporter, depsgraph, scene_props, shape)

    # Add some shapes at the end that are required by some nodes in the node tree

    if uses_pointiness(node_tree):
        # Note: Since Blender still does not make use of the vertex alpha channel
        # as of 2.82, we use it to store the pointiness information.
        pointiness_shape = input_shape + "_pointiness"
        prefix = "scene.shapes." + pointiness_shape + "."
        scene_props.Set(pyluxcore.Property(prefix + "type", "pointiness"))
        scene_props.Set(pyluxcore.Property(prefix + "source", shape))
        shape = pointiness_shape

    _uses_random_per_island_uniform_float = uses_random_per_island_uniform_float(node_tree)
    _uses_random_per_island_int = uses_random_per_island_int(node_tree)
    if _uses_random_per_island_uniform_float or _uses_random_per_island_int:
        island_aov_index = TriAOVDataIndices.RANDOM_PER_ISLAND_INT

        if not _uses_random_per_island_int:
            # We don't need the int result, so use the float index for it so it gets overwrittten to save memory
            island_aov_index = TriAOVDataIndices.RANDOM_PER_ISLAND_FLOAT

        island_aov_shape = input_shape + "_island_aov"
        prefix = "scene.shapes." + island_aov_shape + "."
        scene_props.Set(pyluxcore.Property(prefix + "type", "islandaov"))
        scene_props.Set(pyluxcore.Property(prefix + "source", shape))
        scene_props.Set(pyluxcore.Property(prefix + "dataindex", island_aov_index))
        shape = island_aov_shape

        if _uses_random_per_island_uniform_float:
            # Used to normalize the island indices from ints to floats in 0..1 range
            random_tri_aov_shape = input_shape + "_random_tri_aov_shape"
            prefix = "scene.shapes." + random_tri_aov_shape + "."
            scene_props.Set(pyluxcore.Property(prefix + "type", "randomtriangleaov"))
            scene_props.Set(pyluxcore.Property(prefix + "source", shape))
            scene_props.Set(pyluxcore.Property(prefix + "srcdataindex", island_aov_index))
            scene_props.Set(pyluxcore.Property(prefix + "dstdataindex", TriAOVDataIndices.RANDOM_PER_ISLAND_FLOAT))
            shape = random_tri_aov_shape

    if needs_edge_detector_shape(node_tree):
        edge_detector_shape = input_shape + "_edge_detector"
        prefix = "scene.shapes." + edge_detector_shape + "."
        scene_props.Set(pyluxcore.Property(prefix + "type", "edgedetectoraov"))
        scene_props.Set(pyluxcore.Property(prefix + "source", shape))
        shape = edge_detector_shape

    return shape


def warn_about_subdivision_levels(obj):
    for modifier in obj.modifiers:
        if modifier.type == "SUBSURF" and modifier.show_viewport:
            if not modifier.show_render:
                LuxCoreErrorLog.add_warning("Subdivision modifier enabled in viewport, but not in final render",
                                            obj_name=obj.name)
            elif modifier.render_levels < modifier.levels:
                LuxCoreErrorLog.add_warning(
                    f"Final render subdivision level ({modifier.render_levels}) smaller than viewport subdivision level ({modifier.levels})",
                    obj_name=obj.name)


def get_material(obj, material_index, depsgraph):
    material_override = depsgraph.view_layer_eval.material_override # the view layer override material
    # Evaluate if the override_exclude checkbox is ticked
    override_exclude = False
    material = None
    if material_index < len(obj.material_slots):
        material = obj.material_slots[material_index].material
    if material is not None:
        node_tree = material.luxcore.node_tree
        if node_tree is not None: # happens e.g. in default cube scene when only cycles nodes are defined
            output_node = get_active_output(node_tree)
            override_exclude = output_node.override_exclude

    if material_override and material is None:
        mat = material_override
    elif material_override and not override_exclude:
        mat = material_override
    elif material_index < len(obj.material_slots):
        mat = material

        if mat is None:
            # Note: material.convert returns the fallback material in this case
            msg = "No material attached to slot %d" % (material_index + 1)
            LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
    else:
        # The object has no material slots
        LuxCoreErrorLog.add_warning("No material defined", obj_name=obj.name)
        # Use fallback material
        mat = None

    return mat
        

def export_material(obj, material_index, exporter, depsgraph, is_viewport_render):
    mat = get_material(obj, material_index, depsgraph)

    if mat:
        # We need the original material, not the evaluated one, otherwise 
        # Blender gives us "NodeTreeUndefined" as mat.node_tree.bl_idname
        mat = mat.original
        
        lux_mat_name, mat_props = material.convert(exporter, depsgraph, mat, is_viewport_render, obj.name)
        node_tree = mat.luxcore.node_tree
        return lux_mat_name, mat_props, node_tree
    else:
        lux_mat_name, mat_props = material.fallback()
        return lux_mat_name, mat_props, None


def make_psys_key(obj, psys, is_instance):
    psys_lib_name = psys.settings.library.name if psys.settings.library else ""
    return obj.name_full + psys.name + psys_lib_name + str(is_instance)


def get_total_particle_count(particle_system, is_viewport_render):
    """
    Note: this function does not return the amount of particles that are actually visible in a given
    frame (because it's hard to find that number), but the maximum number the particle system will ever create.
    """
    settings = particle_system.settings

    if (settings.render_type in {"NONE", "HALO", "LINE"}
            or (settings.type == "HAIR" and settings.render_type == "PATH")
            or (is_viewport_render and settings.display_method != "RENDER")):
        return 0

    particle_count = settings.count
    if is_viewport_render:
        particle_count *= settings.display_percentage / 100
    if settings.child_type != "NONE":
        particle_count *= settings.child_percent if is_viewport_render else settings.rendered_child_count
    return particle_count


@lru_cache(maxsize=32)
def supports_live_transform(particle_system):
    if not particle_system:
        return True
    total_particles = get_total_particle_count(particle_system, True)
    return total_particles <= MAX_PARTICLES_FOR_LIVE_TRANSFORM


def _update_stats(engine, current_obj_name, extra_obj_info, current_index, total_object_count):
    engine.update_stats("Export", f"Object: {current_obj_name}{extra_obj_info} ({current_index}/{total_object_count})")
    engine.update_progress(current_index / total_object_count)


def get_obj_count_estimate(depsgraph):
    # This is faster than len(depsgraph.object_instances)
    # TODO: count dupliverts and dupliframes
    obj_count = len(depsgraph.objects)
    for obj in depsgraph.objects:
        try:
            for psys in obj.particle_systems:
                obj_count += get_total_particle_count(psys, False)
        except AttributeError:
            pass
    return obj_count


class Duplis:
    def __init__(self, exported_obj):
        self.exported_obj = exported_obj
        self.matrices = array("f", [])
        self.object_ids = array("I", [])

    def get_count(self):
        return len(self.object_ids)


class ObjectCache2:
    def __init__(self):
        self.exported_objects = {}
        self.exported_meshes = {}
        self.exported_hair = {}

    def first_run(self, exporter, depsgraph, view_layer, engine, luxcore_scene, scene_props, context):
        is_viewport_render = bool(context)
        instances = {}

        if engine:
            obj_count_estimate = max(1, get_obj_count_estimate(depsgraph))

        # Particle system counts might have changed
        supports_live_transform.cache_clear()

        for index, dg_obj_instance in enumerate(depsgraph.object_instances):
            obj = dg_obj_instance.object

            if (dg_obj_instance.is_instance
                    and not (is_viewport_render and supports_live_transform(dg_obj_instance.particle_system))
                    and obj.type in MESH_OBJECTS):
                # This code is optimized for large amounts of duplis. Drawback is that objects generated from this
                # code can't be transformed later in a viewport render session (due to BlendLuxCore implementation
                # reasons, not because of LuxCore)
                if engine and index % 5000 == 0:
                    if engine.test_break():
                        return None
                    _update_stats(engine, obj.name, " (dupli)", index, obj_count_estimate)

                try:
                    # The code in this try block is performance-critical, as it is
                    # executed most often when exporting millions of instances.
                    duplis = instances[obj.original.as_pointer()]
                    # If duplis is None, then a non-exportable object like a curve with zero faces is being duplicated
                    if duplis:
                        obj_id = dg_obj_instance.object.original.luxcore.id
                        if obj_id == -1:
                            obj_id = dg_obj_instance.random_id & 0xfffffffe
                        duplis.object_ids.append(obj_id)
                        # We need a copy of matrix_world here, not sure why, but if we don't
                        # make a copy, we only get an identity matrix in C++
                        duplis.matrices.extend(pyluxcore.BlenderMatrix4x4ToList(dg_obj_instance.matrix_world.copy()))
                except KeyError:
                    if engine:
                        if engine.test_break():
                            return None
                        _update_stats(engine, obj.name, " (dupli)", index, obj_count_estimate)
                    exported_obj = self._convert_obj(exporter, dg_obj_instance, obj, depsgraph, luxcore_scene,
                                                     scene_props, is_viewport_render, view_layer, engine)
                    if exported_obj:
                        # Note, the transformation matrix and object ID of this first instance is not added
                        # to the duplication list, since it already exists in the scene
                        instances[obj.original.as_pointer()] = Duplis(exported_obj)
                    else:
                        # Could not export the object, happens e.g. with curve objects with zero faces
                        instances[obj.original.as_pointer()] = None
            else:
                # This code is for singular objects and for duplis that should be movable later in a viewport render
                if not utils.is_instance_visible(dg_obj_instance, obj, context):
                    continue

                if engine:
                    if engine.test_break():
                        return None
                    _update_stats(engine, obj.name, "", index, obj_count_estimate)

                self._convert_obj(exporter, dg_obj_instance, obj, depsgraph, luxcore_scene,
                                  scene_props, is_viewport_render, view_layer, engine)

        #self._debug_info()
        return instances

    def duplicate_instances(self, instances, luxcore_scene, stats):
        """
        We can only duplicate the instances *after* the scene_props were parsed so the base
        objects are available for luxcore_scene. Needs to happen before this method is called.
        """
        start_time = time()
        
        for duplis in instances.values():
            if duplis is None:
                # If duplis is None, then a non-exportable object like a curve with zero faces is being duplicated
                continue

            if duplis.get_count() == 0:
                # Only one instance was created (and is already present in the luxcore_scene), nothing to duplicate
                continue

            for part in duplis.exported_obj.parts:
                src_name = part.lux_obj
                dst_name = src_name + "dupli"
                luxcore_scene.DuplicateObject(src_name, dst_name, duplis.get_count(), duplis.matrices, duplis.object_ids)

                # TODO: support steps and times (motion blur)
                # steps = 0 # TODO
                # times = array("f", [])
                # luxcore_scene.DuplicateObject(src_name, dst_name, count, steps, times, transformations)
        
        if stats:
            stats.export_time_instancing.value = time() - start_time

    def _debug_info(self):
        print("Objects in cache:", len(self.exported_objects))
        print("Meshes in cache:", len(self.exported_meshes))
        # for key, exported_mesh in self.exported_meshes.items():
        #     if exported_mesh:
        #         print(key, exported_mesh.mesh_definitions)
        #     else:
        #         print(key, "mesh is None")

    def _get_mesh_key(self, obj, use_instancing, is_viewport_render=True):
        # Important: we need the data of the original object, not the evaluated one.
        # The instancing state has to be part of the key because a non-instanced mesh
        # has its transformation baked-in and can't be used by other instances.
        modified = utils.has_deforming_modifiers(obj.original)
        source = obj.original.data if (use_instancing and not (modified or obj.type == "META")) else obj.original
        key = utils.get_luxcore_name(source, is_viewport_render)
        if use_instancing:
            key += "_instance"
        return key

    def _convert_obj(self, exporter, dg_obj_instance, obj, depsgraph, luxcore_scene,
                     scene_props, is_viewport_render, view_layer=None, engine=None):
        """ Convert one DepsgraphObjectInstance amd keep track of it with self.exported_objects """

        if obj.data is None:
            return None
        warn_about_subdivision_levels(obj)

        obj_key = utils.make_key_from_instance(dg_obj_instance)
        exported_stuff = None
        props = pyluxcore.Properties()

        if dg_obj_instance.show_self:
            if obj.type in MESH_OBJECTS:
                if obj.type == 'CURVES' and not obj.data == None:
                    if obj.data.rna_type.name == 'Hair Curves':
                        visible_to_cam = utils.visible_to_camera(dg_obj_instance, is_viewport_render, view_layer)
                        is_for_duplication = is_viewport_render or dg_obj_instance.is_instance
                        lux_shape = convert_hair_curves(exporter, depsgraph, obj, obj_key, luxcore_scene, is_for_duplication)
                        if lux_shape:
                            mat = obj.data.materials[0]
                            if mat:
                                node_tree = mat.luxcore.node_tree
                                if node_tree:
                                    lux_shape = define_shapes(lux_shape, node_tree, exporter, depsgraph, scene_props)

                            self.exported_hair[obj_key] = lux_shape
                        if lux_shape:
                            lux_mat, mat_props, node_tree = export_material(obj, 0, exporter, depsgraph,
                                                                            is_viewport_render)
                            scene_props.Set(mat_props)
                            set_hair_props(scene_props, lux_shape, lux_shape, lux_mat, visible_to_cam,
                                        is_for_duplication, dg_obj_instance.matrix_world, False)

                        # TODO handle case when exported_stuff is None
                        #  (we'll have to create a new ExportedObject just for the hair mesh)
                        if exported_stuff and lux_shape:
                            # Should always be the case because lights can't have particle systems
                            assert isinstance(exported_stuff, ExportedObject)
                            exported_stuff.parts.append(ExportedPart(lux_shape, lux_shape, lux_mat))
                else:

                    exported_stuff = self._convert_mesh_obj(exporter, dg_obj_instance, obj, obj_key, depsgraph,
                                                        luxcore_scene, scene_props, is_viewport_render, view_layer)
                if exported_stuff:
                    props = exported_stuff.get_props()
            elif obj.type == "LIGHT":
                props, exported_stuff = light.convert_light(exporter, obj, obj_key, depsgraph, luxcore_scene,
                                                            dg_obj_instance.matrix_world.copy(), is_viewport_render)

        # Convert hair
        for psys in obj.particle_systems:
            settings = psys.settings

            if psys.particles and settings.type == "HAIR" and settings.render_type == "PATH":
                # Can't use the memory address of the psys as key because it changes
                # when the psys is updated (e.g. because some hair moves)
                is_for_duplication = is_viewport_render or dg_obj_instance.is_instance
                psys_key = make_psys_key(obj, psys, is_for_duplication)
                lux_obj = make_hair_shape_name(obj_key, psys)
                visible_to_cam = utils.visible_to_camera(dg_obj_instance, is_viewport_render, view_layer)
                mat_index = get_hair_material_index(psys)

                try:
                    lux_shape = self.exported_hair[psys_key]
                except KeyError:
                    lux_shape = convert_hair(exporter, obj, obj_key, psys, depsgraph, luxcore_scene,
                                             scene_props, is_viewport_render, is_for_duplication,
                                             dg_obj_instance.matrix_world, visible_to_cam, engine)
                    if lux_shape:
                        mat = get_material(obj, mat_index, depsgraph)
                        if mat:
                            node_tree = mat.luxcore.node_tree
                            if node_tree:
                                lux_shape = define_shapes(lux_shape, node_tree, exporter, depsgraph, scene_props)
                        
                        self.exported_hair[psys_key] = lux_shape
                        
                if lux_shape:
                    lux_mat, mat_props, node_tree = export_material(obj, mat_index, exporter, depsgraph,
                                                                    is_viewport_render)
                    scene_props.Set(mat_props)
                    set_hair_props(scene_props, lux_obj, lux_shape, lux_mat, visible_to_cam,
                                is_for_duplication, dg_obj_instance.matrix_world,
                                settings.luxcore.hair.instancing == "enabled")

                # TODO handle case when exported_stuff is None
                #  (we'll have to create a new ExportedObject just for the hair mesh)
                if exported_stuff and lux_shape:
                    # Should always be the case because lights can't have particle systems
                    assert isinstance(exported_stuff, ExportedObject)
                    exported_stuff.parts.append(ExportedPart(lux_obj, lux_shape, lux_mat))

        if exported_stuff:
            scene_props.Set(props)
            self.exported_objects[obj_key] = exported_stuff

        return exported_stuff

    def _convert_mesh_obj(self, exporter, dg_obj_instance, obj, obj_key, depsgraph,
                          luxcore_scene, scene_props, is_viewport_render, view_layer):
        transform = dg_obj_instance.matrix_world

        # Objects with displacement in the node tree are instanced to avoid discrepancies between viewport and final render
        use_instancing = is_viewport_render or dg_obj_instance.is_instance or utils.can_share_mesh(obj.original) \
                         or (exporter.motion_blur_enabled and obj.luxcore.enable_motion_blur) or uses_displacement(obj)

        mesh_key = self._get_mesh_key(obj, use_instancing, is_viewport_render)

        if use_instancing and mesh_key in self.exported_meshes:
            exported_mesh = self.exported_meshes[mesh_key]
            loaded_from_cache = True
        else:
            exported_mesh = mesh_converter.convert(obj, mesh_key, depsgraph, luxcore_scene,
                                                   is_viewport_render, use_instancing, transform, exporter)
            self.exported_meshes[mesh_key] = exported_mesh
            loaded_from_cache = False

        if exported_mesh:
            mat_names = []
            for idx, (shape_name, mat_index) in enumerate(exported_mesh.mesh_definitions):
                shape = shape_name
                lux_mat_name, mat_props, node_tree = export_material(obj, mat_index, exporter, depsgraph, is_viewport_render)
                scene_props.Set(mat_props)
                mat_names.append(lux_mat_name)

                # Meshes in the cache already have the shapes added.
                # (This assumes that the instances use the same materials as the original mesh)
                if node_tree and not loaded_from_cache:
                    warn_about_missing_uvs(obj, node_tree)
                    shape = define_shapes(shape, node_tree, exporter, depsgraph, scene_props)

                exported_mesh.mesh_definitions[idx] = [shape, mat_index]

            obj_transform = transform.copy() if use_instancing else None
            obj_id = utils.make_object_id(dg_obj_instance)

            return ExportedObject(obj_key, exported_mesh.mesh_definitions, mat_names, obj_transform,
                                  utils.visible_to_camera(dg_obj_instance, is_viewport_render, view_layer), obj_id)

    def diff(self, depsgraph):
        only_scene = len(depsgraph.updates) == 1 and isinstance(depsgraph.updates[0].id, bpy.types.Scene)
        return depsgraph.id_type_updated("OBJECT") and not only_scene

    def update(self, exporter, depsgraph, luxcore_scene, scene_props, context):
        is_viewport_render = bool(context)
        redefine_objs_with_these_mesh_keys = []
        # Always instance in viewport so we can move objects around
        use_instancing = True

        # Geometry updates (mesh edit, modifier edit etc.)
        if depsgraph.id_type_updated("OBJECT"):
            for dg_update in depsgraph.updates:
                if dg_update.is_updated_geometry and isinstance(dg_update.id, bpy.types.Object):
                    obj = dg_update.id
                    if not utils.is_obj_visible(obj) or not obj.visible_in_viewport_get(context.space_data):
                        continue

                    if obj.type in MESH_OBJECTS:
                        if obj.type == 'CURVES' and not obj.data == None:
                            if obj.data.rna_type.name == 'Hair Curves':
                                obj_key = utils.make_key(obj)
                                del self.exported_hair[obj_key]
                        else:
                            mesh_key = self._get_mesh_key(obj, use_instancing)

                            # if mesh_key not in self.exported_meshes:
                            # TODO this can happen if a deforming modifier is added
                            #  to an already-exported object. how to handle this case?

                            transform = None  # In viewport render, everything is instanced
                            exported_mesh = mesh_converter.convert(obj, mesh_key, depsgraph, luxcore_scene,
                                                                   is_viewport_render, use_instancing, transform)

                            if exported_mesh:
                                for i in range(len(exported_mesh.mesh_definitions)):
                                    shape, mat_index = exported_mesh.mesh_definitions[i]
                                    mat = get_material(obj, mat_index, depsgraph)

                                    if mat:
                                        node_tree = mat.luxcore.node_tree
                                        if node_tree:
                                            shape = define_shapes(shape, node_tree, exporter, depsgraph, scene_props)

                                    exported_mesh.mesh_definitions[i] = shape, mat_index

                            self.exported_meshes[mesh_key] = exported_mesh

                            # We arrive here not only when the mesh is edited, but also when the material
                            # of the object is changed in Blender. In this case we have to re-define all
                            # objects using this mesh (just the properties, the mesh is not re-exported).
                            redefine_objs_with_these_mesh_keys.append(mesh_key)

                        # Re-export hair systems of objects with updated geometry
                        for psys in obj.particle_systems:
                            settings = psys.settings

                            if psys.particles and settings.type == "HAIR" and settings.render_type == "PATH":
                                # Can't use the memory address of the psys as key because it changes
                                # when the psys is updated (e.g. because some hair moves)
                                psys_key = make_psys_key(obj, psys, True)
                                del self.exported_hair[psys_key]
                    elif obj.type == "LIGHT":
                        obj_key = utils.make_key(obj)
                        props, exported_stuff = light.convert_light(exporter, obj, obj_key, depsgraph, luxcore_scene,
                                                                    obj.matrix_world.copy(), is_viewport_render)
                        if exported_stuff:
                            self.exported_objects[obj_key] = exported_stuff
                            scene_props.Set(props)

        # TODO maybe not loop over all instances, instead only loop over updated
        #  objects and check if they have a particle system that needs to be updated?
        #  Would be better for performance with many particles, however I'm not sure
        #  we can find all instances corresponding to one particle system?

        # Currently, every update that doesn't require a mesh re-export happens here
        for dg_obj_instance in depsgraph.object_instances:
            if not supports_live_transform(dg_obj_instance.particle_system):
                continue

            obj = dg_obj_instance.object
            if not utils.is_instance_visible(dg_obj_instance, obj, context):
                continue

            obj_key = utils.make_key_from_instance(dg_obj_instance)
            mesh_key = self._get_mesh_key(obj, use_instancing)

            if (obj_key in self.exported_objects and obj.type != "LIGHT") and not mesh_key in redefine_objs_with_these_mesh_keys:
                exported_obj = self.exported_objects[obj_key]
                updated = False

                if exported_obj.transform != dg_obj_instance.matrix_world:
                    exported_obj.transform = dg_obj_instance.matrix_world.copy()
                    updated = True

                obj_id = utils.make_object_id(dg_obj_instance)
                if exported_obj.obj_id != obj_id:
                    exported_obj.obj_id = obj_id
                    updated = True

                if exported_obj.visible_to_camera != utils.visible_to_camera(dg_obj_instance, is_viewport_render):
                    exported_obj.visible_to_camera = utils.visible_to_camera(dg_obj_instance, is_viewport_render)
                    updated = True

                if updated:
                    scene_props.Set(exported_obj.get_props())
            else:
                # Object is new and not in LuxCore yet, or it is a light, do a full export
                self._convert_obj(exporter, dg_obj_instance, obj, depsgraph,
                                  luxcore_scene, scene_props, is_viewport_render)

        #self._debug_info()

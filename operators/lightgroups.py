import bpy
from bpy.props import IntProperty
from ..utils import node as utils_node


class LUXCORE_OT_add_lightgroup(bpy.types.Operator):
    bl_idname = "luxcore.add_lightgroup"
    bl_label = "Add Light Group"
    bl_description = "Add a light group"
    bl_options = {"UNDO"}

    def execute(self, context):
        groups = context.scene.luxcore.lightgroups
        groups.add()
        return {"FINISHED"}


class LUXCORE_OT_remove_lightgroup(bpy.types.Operator):
    bl_idname = "luxcore.remove_lightgroup"
    bl_label = "Remove Light Group"
    bl_description = "Remove this light group"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        groups = context.scene.luxcore.lightgroups
        groups.remove(self.index)
        return {"FINISHED"}


class LUXCORE_OT_select_objects_in_lightgroup(bpy.types.Operator):
    bl_idname = "luxcore.select_objects_in_lightgroup"
    bl_label = "Select Objects"
    bl_description = ("Select all objects that are affected by this light "
                      "group (lights and meshes with emissive material)\n"
                      "Selection will be added to the current selection")
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        group_name = context.scene.luxcore.lightgroups.custom[self.index].name
        relevant_node_types = {
            "LuxCoreNodeMatEmission",
            "LuxCoreNodeVolClear",
            "LuxCoreNodeVolHomogeneous",
            "LuxCoreNodeVolHeterogeneous",
        }

        # There are probably far less materials than objects in the scene
        materials_in_group = set()
        for mat in bpy.data.materials:
            node_tree = mat.luxcore.node_tree
            if not node_tree or mat.luxcore.use_cycles_nodes:
                continue

            for node in utils_node.find_nodes_multi(node_tree, relevant_node_types, follow_pointers=True):
                if node.lightgroup == group_name:
                    materials_in_group.add(mat)
                    break

        for obj in context.scene.objects:
            if obj.type == "LIGHT" and obj.data.luxcore.lightgroup == group_name:
                obj.select_set(True, view_layer=context.view_layer)
            else:
                for mat_slot in obj.material_slots:
                    if mat_slot.material in materials_in_group:
                        obj.select_set(True, view_layer=context.view_layer)
                        break

        return {"FINISHED"}

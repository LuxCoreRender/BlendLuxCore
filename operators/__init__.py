import bpy


class LUXCORE_OT_material_new(bpy.types.Operator):
    bl_idname = "luxcore.material_new"
    bl_label = "New"
    bl_description = "Create a material and node tree"

    def execute(self, context):
        mat = bpy.data.materials.new(name="Material")
        node_tree = bpy.data.node_groups.new(name=mat.name, type="luxcore_material_nodes")
        mat.luxcore.node_tree = node_tree

        obj = context.active_object
        if obj.material_slots:
            obj.material_slots[obj.active_material_index].material = mat
        else:
            obj.data.materials.append(mat)

        return {"FINISHED"}
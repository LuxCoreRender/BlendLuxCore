import bpy
from bpy.props import IntProperty, StringProperty, EnumProperty
from .. import utils
from .utils import (
    poll_object, poll_material, init_mat_node_tree, make_nodetree_name,
    LUXCORE_OT_set_node_tree, 
)


class LUXCORE_OT_proxy_new(bpy.types.Operator):
    bl_idname = "luxcore.proxy_new"
    bl_label = "New"
    bl_description = "Create a new proxy object"

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        obj = context.active_object
        obj.luxcore.use_proxy = True
        print("Create Proxy for Object:", obj.name)
        return {"FINISHED"}

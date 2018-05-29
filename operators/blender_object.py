import bpy
from bpy.props import IntProperty, StringProperty, EnumProperty
from .. import utils
from ..bin import pyluxcore
from .utils import (
    poll_object, poll_material, init_mat_node_tree, make_nodetree_name,
    LUXCORE_OT_set_node_tree, 
)


class LUXCORE_OT_proxy_new(bpy.types.Operator):
    bl_idname = "luxcore.proxy_new"
    bl_label = "New"
    bl_description = "Create a new proxy object"



    # hidden properties
    directory = bpy.props.StringProperty(name = 'PLY directory')
    filter_glob = bpy.props.StringProperty(default = '*.ply', options = {'HIDDEN'})
    use_filter = bpy.props.BoolProperty(default = True, options = {'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}        

    def execute(self, context):
        obj = context.active_object

        #TODO: Support other object types
        if obj.type in ['MESH']:
            if obj.data.users > 1:
                print("[Object: %s] Can't make proxy from multiuser mesh" % obj.name)
                #TODO: Raise error in log
                return {"FINISHED"}

            proxy = obj
            obj = proxy.copy()
            obj.data = proxy.data.copy()
            context.scene.objects.link(obj)

            # rename object
            obj.name = proxy.name
            proxy.name = obj.name + '_lux_proxy'

            # TODO: accept custom parameters for decimate modifier
            decimate = proxy.modifiers.new('proxy_decimate', 'DECIMATE')
            decimate.ratio = 0.005
                        
            proxy.select = True
            context.scene.objects.active = proxy
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=decimate.name)
                        
            proxy.luxcore.use_proxy = True

            bpy.ops.object.select_all(action='DESELECT')
            obj.select = True
            context.scene.objects.active = obj
            
            # clear parent
            bpy.ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')

            mesh = obj.to_mesh(context.scene, True, 'RENDER')
            
            # Export object into PLY files via pyluxcore functions
            luxcore_scene = pyluxcore.Scene()
            
            faces = mesh.tessfaces[0].as_pointer()
            vertices = mesh.vertices[0].as_pointer()

            uv_textures = mesh.tessface_uv_textures
            active_uv = utils.find_active_uv(uv_textures)
            if active_uv and active_uv.data:
                texCoords = active_uv.data[0].as_pointer()
            else:
                texCoords = 0

            vertex_color = mesh.tessface_vertex_colors.active
            if vertex_color:
                vertexColors = vertex_color.data[0].as_pointer()
            else:
                vertexColors = 0

            transformation = utils.matrix_to_list(obj.matrix_world, context.scene, apply_worldscale=True)
            
            mesh_definitions = luxcore_scene.DefineBlenderMesh(obj.name, len(mesh.tessfaces), faces, len(mesh.vertices),
                                           vertices, texCoords, vertexColors, transformation)

            
            bpy.ops.object.select_all(action='DESELECT')
            obj.select = True
            context.scene.objects.active = obj
            bpy.ops.object.delete()
            
            print("Export high resolution geometry data into PLY files...")
            for [name, mat] in mesh_definitions:
                filepath = self.directory + name + ".ply"
                luxcore_scene.SaveMesh("Mesh-"+name, filepath);                
                proxy.luxcore.proxies.add()
                new = proxy.luxcore.proxies[-1]
                new.name = name
                new.filepath = self.directory + name + ".ply"
                print("Saved ", self.directory + name + ".ply")
            

            bpy.ops.object.select_all(action='DESELECT')
            proxy.select = True
            context.scene.objects.active = proxy
        
        return {"FINISHED"}

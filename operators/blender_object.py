import bpy
from bpy.props import FloatProperty
from .. import utils
from ..bin import pyluxcore
from .utils import poll_object

# TODO:
# - Undo handling
# - Support all surface types, not only MESH
# - Test with all kinds of objects, curves, text, empty etc.
# - Allow multiple selected objects to be converted


def remove(data):
    if data is None:
        return

    if data.users:
        print("Could not remove datablock %s because it has users (%d)" % (data.name, data.users))
        return

    if type(data) == bpy.types.Mesh:
        bpy.data.meshes.remove(data, do_unlink=False)
    elif type(data) in {bpy.types.Curve, bpy.types.TextCurve, bpy.types.SurfaceCurve}:
        bpy.data.curves.remove(data, do_unlink=False)
    elif type(data) == bpy.types.MetaBall:
        bpy.data.metaballs.remove(data, do_unlink=False)
    else:
        print("Could not remove datablock %s (type %s)" % (data.name, type(data)))


def LUXCORE_OT_use_proxy_switch(self, context):
    obj = context.active_object
    transformation = obj.matrix_world
    
    if not obj.luxcore.use_proxy:
        if len(obj.luxcore.proxies) > 0:            
            bpy.ops.object.select_all(action='DESELECT')

            # Reload high res object
            for p in obj.luxcore.proxies:
                bpy.ops.import_mesh.ply(filepath=p.filepath)
                
            for s in context.selected_objects:
                matIndex = obj.luxcore.proxies[s.name].matIndex
                mat = obj.material_slots[matIndex].material
                s.data.materials.append(mat)

            bpy.ops.object.join()
            context.active_object.matrix_world = transformation
            context.active_object.name = context.active_object.name[:-3]

            bpy.ops.object.select_all(action='DESELECT')
            obj.select = True
            bpy.ops.object.delete()


class LUXCORE_OT_proxy_new(bpy.types.Operator):
    bl_idname = "luxcore.proxy_new"
    bl_label = "New"
    bl_description = "Create a new proxy object"

    decimate_ratio = bpy.props.FloatProperty(name="Proxy Mesh Quality",
                                             description="Decimate ratio that is applied to the preview mesh",
                                             default=5, soft_min=0.1, soft_max=50, max=100,
                                             subtype='PERCENTAGE')

    # hidden properties
    directory = bpy.props.StringProperty(name="PLY directory")
    filter_glob = bpy.props.StringProperty(default="*.ply", options={'HIDDEN'})
    use_filter = bpy.props.BoolProperty(default=True, options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def invoke(self, context, event):
        obj = context.active_object
        if obj.data.users > 1:
            context.scene.luxcore.errorlog.add_error("[Object: %s] Can't make proxy from multiuser mesh" % obj.name)
            return {'CANCELLED'}
            
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}        

    def execute(self, context):
        obj = context.active_object

        # TODO: Support other object types
        if obj.type in {'MESH'}:
            proxy = self.make_lowpoly_proxy(obj, context.scene, self.decimate_ratio / 100)

            # Clear parent
            bpy.ops.object.select_all(action='DESELECT')
            obj.select = True
            context.scene.objects.active = obj
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

            # Create high-resolution mesh with applied modifiers
            mesh = obj.to_mesh(context.scene, True, 'RENDER')
            mesh_name = utils.to_luxcore_name(obj.name)
            # Delete the original object, we don't need it anymore
            obj_data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            remove(obj_data)

            # Export object into PLY files via pyluxcore functions
            luxcore_scene = pyluxcore.Scene()
            mesh_definitions = self.define_mesh(luxcore_scene, mesh, mesh_name)
            # Delete the temporary mesh (don't have to unlink because it was never "registered" in bpy.data)
            bpy.data.meshes.remove(mesh, do_unlink=False)

            print("[Create Proxy] Exporting high resolution geometry data into PLY files...")
            for name, mat in mesh_definitions:
                filepath = self.directory + name + ".ply"
                luxcore_scene.SaveMesh("Mesh-" + name, filepath)
                new = proxy.luxcore.proxies.add()
                new.name = name
                new.matIndex = mat
                new.filepath = filepath
                print("[Create Proxy] Saved", filepath)
            
            bpy.ops.object.select_all(action='DESELECT')
            proxy.select = True
            context.scene.objects.active = proxy
        return {"FINISHED"}

    def make_lowpoly_proxy(self, obj, scene, decimate_ratio):
        print("[Create Proxy] Copying object", obj.name)
        # TODO we need to make sure that we create a MESH object, even if source is e.g. a CURVE
        proxy = obj.copy()
        scene.objects.link(proxy)
        proxy.name = obj.name + "_lux_proxy"

        decimate = proxy.modifiers.new("proxy_decimate", 'DECIMATE')
        decimate.ratio = decimate_ratio

        print("[Create Proxy] Creating low resolution proxy object")
        proxy_mesh = proxy.to_mesh(scene, True, 'PREVIEW')
        # to_mesh has applied the modifiers, we don't need them anymore
        proxy.modifiers.clear()
        # Use the low res mesh with applied modifiers instead of the original high res mesh
        proxy.data = proxy_mesh

        proxy.luxcore.use_proxy = True
        return proxy

    def define_mesh(self, luxcore_scene, mesh, name):
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

        return luxcore_scene.DefineBlenderMesh(name, len(mesh.tessfaces), faces,
                                               len(mesh.vertices), vertices,
                                               texCoords, vertexColors, None)


class LUXCORE_OT_proxy_add(bpy.types.Operator):
    bl_idname = "luxcore.proxy_add"
    bl_label = "Add"
    bl_description = "Add an object to the proxy list"

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):        
        obj = context.active_object
        new = obj.luxcore.proxies.add()
        new.name = obj.name  
        obj.luxcore.proxies.update()        
        return {"FINISHED"}


class LUXCORE_OT_proxy_remove(bpy.types.Operator):
    bl_idname = "luxcore.proxy_remove"
    bl_label = "Remove"
    bl_description = "Remove an object from the proxy list"

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):        
        obj = context.active_object
        obj.luxcore.proxies.remove(len(obj.luxcore.proxies)-1)
        obj.luxcore.proxies.update()
        
        return {"FINISHED"}

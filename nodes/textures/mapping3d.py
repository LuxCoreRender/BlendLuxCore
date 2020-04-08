import bpy
from bpy.props import FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, StringProperty, IntProperty
from mathutils import Matrix
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexMapping3D(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "3D Mapping"
    bl_width_default = 260

    def update_uvmap(self, context):
        obj = context.object
        if obj and obj.data and obj.type == "MESH":
            for i, e in enumerate(obj.data.uv_layers.keys()):
                if e == self.uvmap:
                    self.uvindex = i
            utils_node.force_viewport_update(self, context)

    mapping_types = [
        ("globalmapping3d", "Global", "World coordinate system", 0),
        ("localmapping3d", "Local", "Object coordinate system", 1),
        ("uvmapping3d", "UV", "Use the UV coordinates of the mesh to map the texture", 2),
    ]
    mapping_type: EnumProperty(update=utils_node.force_viewport_update, name="Mapping", items=mapping_types, default="globalmapping3d")
    translate: FloatVectorProperty(update=utils_node.force_viewport_update, name="Translate", subtype="TRANSLATION", description="Moves the texture")
    rotate: FloatVectorProperty(update=utils_node.force_viewport_update, name="Rotate", unit="ROTATION", default=(0, 0, 0), subtype="EULER",
                                 description="Rotates the texture")
    scale: FloatVectorProperty(update=utils_node.force_viewport_update, name="Scale", default=(1.0, 1.0, 1.0), subtype="XYZ",
                                description="Scales the texture")
    uniform_scale: FloatProperty(update=utils_node.force_viewport_update, name="", default=1.0,
                                  description="Scales the texture uniformly along all axis")
    use_uniform_scale: BoolProperty(update=utils_node.force_viewport_update, name="Uniform", default=False,
                                     description="Use the same scale value for all axis")
    uvmap: StringProperty(update=update_uvmap, name="UV Map")
    uvindex: IntProperty(name="UV Index", default=0)

    def init(self, context):
        # Instead of creating a new mapping, the user can also
        # manipulate an existing mapping
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping (optional)")

        self.outputs.new("LuxCoreSocketMapping3D", "3D Mapping")

    def draw_buttons(self, context, layout):
        # Show the mapping type dropdown only when mapping type is not
        # already set by previous mapping node
        if not self.inputs["3D Mapping (optional)"].is_linked:
            layout.prop(self, "mapping_type")

            if self.mapping_type == "uvmapping3d":
                utils_node.draw_uv_info(context, layout)
                obj = context.object
                if obj and obj.data and obj.type == "MESH":
                    layout.prop_search(self, "uvmap", obj.data, "uv_layers", text="UV Map", icon='GROUP_UVS')

        row = layout.row()

        row.column().prop(self, "translate")
        row.column().prop(self, "rotate")

        scale_column = row.column()
        if self.use_uniform_scale:
            scale_column.label(text="Scale:")
            scale_column.prop(self, "uniform_scale")
        else:
            scale_column.prop(self, "scale")

        scale_column.prop(self, "use_uniform_scale")

    def export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        mapping_type, uvindex, input_mapping = self.inputs["3D Mapping (optional)"].export(exporter, depsgraph, props)
        # Use the mapping type of this node only when mapping type is not
        # already set by previous mapping node
        if not self.inputs["3D Mapping (optional)"].is_linked:
            mapping_type = self.mapping_type
            uvindex = self.uvindex

        # create a location matrix
        tex_loc = Matrix.Translation(self.translate)

        # create an identity matrix
        tex_sca = Matrix()
        tex_sca[0][0] = self.uniform_scale if self.use_uniform_scale else self.scale[0]  # X
        tex_sca[1][1] = self.uniform_scale if self.use_uniform_scale else self.scale[1]  # Y
        tex_sca[2][2] = self.uniform_scale if self.use_uniform_scale else self.scale[2]  # Z

        # Prevent "singular matrix in matrixinvert" error (happens if a scale axis equals 0)
        for i in range(3):
            if tex_sca[i][i] == 0:
                tex_sca[i][i] = 0.0000000001

        # create a rotation matrix
        tex_rot0 = Matrix.Rotation(self.rotate[0], 4, "X")
        tex_rot1 = Matrix.Rotation(self.rotate[1], 4, "Y")
        tex_rot2 = Matrix.Rotation(self.rotate[2], 4, "Z")
        tex_rot = tex_rot0 @ tex_rot1 @ tex_rot2

        # combine transformations
        transformation = tex_loc @ tex_rot @ tex_sca

        # Transform input matrix
        output_mapping = input_mapping @ transformation

        return mapping_type, uvindex, output_mapping

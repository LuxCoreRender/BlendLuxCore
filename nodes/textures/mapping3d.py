import bpy
from bpy.props import FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, StringProperty, IntProperty
from mathutils import Matrix
import math
from ..base import LuxCoreNodeTexture
from ... import utils
from ...utils import node as utils_node
from ... import icons
from ...export.caches.object_cache import TriAOVDataIndices


class LuxCoreNodeTexMapping3D(LuxCoreNodeTexture, bpy.types.Node):
    bl_label = "3D Mapping"
    bl_width_default = 260

    def update_uvmap(self, context):
        obj = context.object
        if obj and obj.data and obj.type == "MESH":
            for i, e in enumerate(obj.data.uv_layers.keys()):
                if e == self.uvmap:
                    self.uvindex = i
            utils_node.force_viewport_update(self, context)

    def update_mapping_type(self, context):
        id = self.inputs.find("3D Mapping (optional)")
        self.inputs[id].enabled = self.mapping_type != "localrandommapping3d"
        if self.mapping_type == "localrandommapping3d" and self.seed_type == "mesh_islands":
            utils_node.force_viewport_mesh_update(self, context)
        else:
            utils_node.force_viewport_update(self, context)

    mapping_types = [
        ("globalmapping3d", "Global", "World coordinate system", 0),
        ("localmapping3d", "Local", "Object coordinate system", 1),
        ("localrandommapping3d", "Random Local", "Object coordinate system with randomization options", 3),
        ("uvmapping3d", "UV", "Use the UV coordinates of the mesh to map the texture", 2),
    ]
    mapping_type: EnumProperty(update=update_mapping_type, name="Type", items=mapping_types, default="globalmapping3d")

    # Shared by globalmapping3d, localmapping3d, uvmapping3d, localrandommapping3d
    translate: FloatVectorProperty(update=utils_node.force_viewport_update, name="Translate", subtype="TRANSLATION", description="Moves the texture")
    rotate: FloatVectorProperty(update=utils_node.force_viewport_update, name="Rotate", unit="ROTATION", default=(0, 0, 0), subtype="EULER",
                                 description="Rotates the texture")
    scale: FloatVectorProperty(update=utils_node.force_viewport_update, name="Scale", default=(1.0, 1.0, 1.0), subtype="XYZ",
                                description="Scales the texture")
    uniform_scale: FloatProperty(update=utils_node.force_viewport_update, name="", default=1.0,
                                  description="Scales the texture uniformly along all axis")
    use_uniform_scale: BoolProperty(update=utils_node.force_viewport_update, name="Uniform", default=False,
                                     description="Use the same scale value for all axis")

    # localrandommapping3d
    seed_types = [
        ("object_id", "Object ID", "Mapping will be different when the object ID is different", 0),
        ("mesh_islands", "Mesh Islands", "Mapping will be different between disconnected mesh islands", 1),
    ]
    # Changes to this property require a mesh re-export in viewport,
    # because it depends on a LuxCore shape to pre-process the data
    seed_type: EnumProperty(update=utils_node.force_viewport_mesh_update, name="Seed", items=seed_types,
                            default="object_id", description="Source of the randomness")

    object_id_offset: IntProperty(update=utils_node.force_viewport_update, name="Object ID Offset", default=0,
                                  description="Use this to create variations between mappings even within the same object ID")

    random_translation: BoolProperty(update=utils_node.force_viewport_update, name="Random Translation", default=True)
    translate_max: FloatVectorProperty(update=utils_node.force_viewport_update, name="Translate Max", subtype="TRANSLATION",
                                       description="Moves the texture")
    random_rotation: BoolProperty(update=utils_node.force_viewport_update, name="Random Rotation", default=True)
    rotate_max: FloatVectorProperty(update=utils_node.force_viewport_update, name="Rotate Max", unit="ROTATION",
                                    default=(math.pi * 2, math.pi * 2, math.pi * 2), subtype="EULER",
                                    description="Rotates the texture")
    random_scale: BoolProperty(update=utils_node.force_viewport_update, name="Random Scale", default=True)
    scale_max: FloatVectorProperty(update=utils_node.force_viewport_update, name="Scale Max", default=(1.0, 1.0, 1.0),
                                   subtype="XYZ",
                                   description="Scales the texture")
    uniform_scale_max: FloatProperty(update=utils_node.force_viewport_update, name="", default=1.0,
                                     description="Scales the texture uniformly along all axis")

    # uvmapping3d
    uvmap: StringProperty(update=update_uvmap, name="UV Map")
    uvindex: IntProperty(name="UV Index", default=0)

    def init(self, context):
        # Instead of creating a new mapping, the user can also
        # manipulate an existing mapping
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping (optional)")

        self.outputs.new("LuxCoreSocketMapping3D", "3D Mapping")

    def draw_buttons(self, context, layout):
        if "3D Mapping (optional)" in self.inputs:
            input_mapping_node = utils_node.get_linked_node(self.inputs["3D Mapping (optional)"])

            if isinstance(input_mapping_node, LuxCoreNodeTexMapping3D) and input_mapping_node.mapping_type == "localrandommapping3d":
                layout.label(text="Random not valid as input!", icon=icons.ERROR)
        else:
            input_mapping_node = None

        # Show the mapping type dropdown only when mapping type is not
        # already set by previous mapping node
        if not input_mapping_node:
            layout.prop(self, "mapping_type")

            if self.mapping_type == "uvmapping3d":
                utils_node.draw_uv_info(context, layout)
                obj = context.object
                if obj and obj.data and obj.type == "MESH":
                    layout.prop_search(self, "uvmap", obj.data, "uv_layers", text="UV Map", icon='GROUP_UVS')

        if self.mapping_type in {"globalmapping3d", "localmapping3d", "uvmapping3d"}:
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
        elif self.mapping_type == "localrandommapping3d":
            layout.prop(self, "seed_type")
            if self.seed_type == "object_id":
                layout.prop(self, "object_id_offset")

            box = layout.box()
            row = box.row()
            row.prop(self, "random_translation")
            row = box.row()
            col = row.column(align=True)
            col.prop(self, "translate", text="Translate Min" if self.random_translation else "Translate")
            col = row.column(align=True)
            col.active = self.random_translation
            col.prop(self, "translate_max")

            box = layout.box()
            row = box.row()
            row.prop(self, "random_rotation")
            row = box.row()
            col = row.column(align=True)
            col.prop(self, "rotate", text="Rotate Min" if self.random_rotation else "Rotate")
            col = row.column(align=True)
            col.active = self.random_rotation
            col.prop(self, "rotate_max")

            box = layout.box()
            row = box.row()
            row.prop(self, "random_scale")
            row.prop(self, "use_uniform_scale", text="Uniform Scale")

            if self.use_uniform_scale:
                row = box.row(align=True)
                row.prop(self, "uniform_scale", text="Min" if self.random_scale else "Scale")
                row = row.row(align=True)
                row.active = self.random_scale
                row.prop(self, "uniform_scale_max", text="Max")
            else:
                row = box.row()
                col = row.column(align=True)
                col.prop(self, "scale", text="Scale Min" if self.random_scale else "Scale")
                col = row.column(align=True)
                col.active = self.random_scale
                col.prop(self, "scale_max")
        else:
            raise NotImplementedError("Unknown 3D mapping type:", self.mapping_type)

    def export_generic(self, exporter, depsgraph, props):
        input_socket = self.inputs["3D Mapping (optional)"]
        if utils_node.get_link(input_socket):
            definitions = input_socket.export(exporter, depsgraph, props)
            mapping_type = definitions["mapping.type"]
            uvindex = definitions["mapping.uvindex"]
            # Needs to be converted back to mathutils.Matrix so we can work with it
            input_mapping = utils.list_to_matrix(definitions["mapping.transformation"])
        else:
            # Use the mapping type of this node only when mapping type is not
            # already set by previous mapping node
            mapping_type = self.mapping_type
            uvindex = self.uvindex
            input_mapping = Matrix()

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

        return {
            "mapping.type": mapping_type,
            "mapping.transformation": utils.luxutils.matrix_to_list(output_mapping),
            # Only used when mapping.type is uvmapping3d
            "mapping.uvindex": uvindex,
        }

    def export_localrandommapping3d(self):
        translate_max = self.translate_max if self.random_translation else self.translate
        rotate_max = self.rotate_max if self.random_rotation else self.rotate
        scale_max = self.scale_max if self.random_scale else self.scale
        uniform_scale_max = self.uniform_scale_max if self.random_scale else self.uniform_scale

        definitions = {
            "mapping.type": "localrandommapping3d",
            # "mapping.transformation": Unused

            "mapping.xrotation": [math.degrees(self.rotate[0]), math.degrees(rotate_max[0])],
            "mapping.yrotation": [math.degrees(self.rotate[1]), math.degrees(rotate_max[1])],
            "mapping.zrotation": [math.degrees(self.rotate[2]), math.degrees(rotate_max[2])],

            "mapping.xtranslate": [self.translate[0], translate_max[0]],
            "mapping.ytranslate": [self.translate[1], translate_max[1]],
            "mapping.ztranslate": [self.translate[2], translate_max[2]],

            "mapping.xyzscale.uniform": self.use_uniform_scale,
            # When uniform scale is enabled, only the xscale property is used, and yscale and zscale are ignored
            "mapping.xscale": [self.uniform_scale, uniform_scale_max] if self.use_uniform_scale else [self.scale[0], scale_max[0]],
            "mapping.yscale": [self.scale[1], scale_max[1]],
            "mapping.zscale": [self.scale[2], scale_max[2]],

            "mapping.uvindex": self.uvindex,
        }

        if self.seed_type == "object_id":
            definitions["mapping.seed.type"] = "object_id_offset"
            definitions["mapping.objectidoffset.value"] = self.object_id_offset
        elif self.seed_type == "mesh_islands":
            definitions["mapping.seed.type"] = "triangle_aov"
            definitions["mapping.triangleaov.index"] = TriAOVDataIndices.RANDOM_PER_ISLAND_INT

        return definitions

    def export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        if self.mapping_type in {"globalmapping3d", "localmapping3d", "uvmapping3d"}:
            return self.export_generic(exporter, depsgraph, props)
        elif self.mapping_type == "localrandommapping3d":
            return self.export_localrandommapping3d()
        else:
            raise NotImplementedError("Unknown 3D mapping type:", self.mapping_type)

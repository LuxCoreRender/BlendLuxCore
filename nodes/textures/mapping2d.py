import bpy
import math
from bpy.props import FloatProperty, FloatVectorProperty, BoolProperty, StringProperty, IntProperty, EnumProperty
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node
from ...ui import icons
from ...export.caches.object_cache import TriAOVDataIndices


class LuxCoreNodeTexMapping2D(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "2D Mapping"
    bl_width_default = 160

    def update_uvmap(self, context):
        if context.object:
            self.uvindex = context.object.data.uv_layers.find(self.uvmap)
        utils_node.force_viewport_update(self, context)

    def update_uniform_scale(self, context):
        self["uscale"] = self.uniform_scale
        self["vscale"] = self.uniform_scale
        utils_node.force_viewport_update(self, context)

    def update_mapping_type(self, context):
        self.inputs["2D Mapping (optional)"].enabled = self.mapping_type == "uvmapping2d"
        if self.mapping_type == "uvrandommapping2d" and self.seed_type == "mesh_islands":
            utils_node.force_viewport_mesh_update(self, context)
        else:
            utils_node.force_viewport_update(self, context)

    mapping_types = [
        ("uvmapping2d", "UV", "Use the UV coordinates of the mesh to map the texture", 0),
        ("uvrandommapping2d", "Randomized UV", "", 1),  # TODO description
    ]
    mapping_type: EnumProperty(update=update_mapping_type, name="Type", items=mapping_types,
                               default="uvmapping2d")

    uvmap: StringProperty(update=update_uvmap, name="UV Map")
    uvindex: IntProperty(name="UV Index", default=0)

    # uvmapping2d
    # TODO descriptions
    use_uniform_scale: BoolProperty(update=utils_node.force_viewport_update, name="Uniform Scale", default=True)
    uniform_scale: FloatProperty(name="UV Scale", default=1, update=update_uniform_scale)
    uscale: FloatProperty(update=utils_node.force_viewport_update, name="U", default=1)
    vscale: FloatProperty(update=utils_node.force_viewport_update, name="V", default=1)
    rotation: FloatProperty(update=utils_node.force_viewport_update, name="Rotation", default=0, min=(-math.pi * 2),
                             max=(math.pi * 2), subtype="ANGLE", unit="ROTATION")
    udelta: FloatProperty(update=utils_node.force_viewport_update, name="U", default=0)
    vdelta: FloatProperty(update=utils_node.force_viewport_update, name="V", default=0)
    center_map: BoolProperty(update=utils_node.force_viewport_update, name="Center Map", default=False)

    # uvrandommapping2d
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

    random_rotation_min: FloatProperty(update=utils_node.force_viewport_update, name="Min",
                                       default=0, min=(-math.pi * 2), max=(math.pi * 2),
                                       subtype="ANGLE", unit="ROTATION")
    random_rotation_max: FloatProperty(update=utils_node.force_viewport_update, name="Max",
                                       default=math.pi * 2, min=(-math.pi * 2), max=(math.pi * 2),
                                       subtype="ANGLE", unit="ROTATION")

    random_uvscale_uniform: BoolProperty(update=utils_node.force_viewport_update, name="Uniform Scale", default=True,
                                         description="If disabled, U and V can be scaled independently")
    random_uscale_min: FloatProperty(update=utils_node.force_viewport_update, name="Min", default=1)
    random_uscale_max: FloatProperty(update=utils_node.force_viewport_update, name="Max", default=1)
    random_vscale_min: FloatProperty(update=utils_node.force_viewport_update, name="Min", default=1)
    random_vscale_max: FloatProperty(update=utils_node.force_viewport_update, name="Max", default=1)

    random_udelta_min: FloatProperty(update=utils_node.force_viewport_update, name="Min", default=0)
    random_udelta_max: FloatProperty(update=utils_node.force_viewport_update, name="Max", default=0)
    random_vdelta_min: FloatProperty(update=utils_node.force_viewport_update, name="Min", default=0)
    random_vdelta_max: FloatProperty(update=utils_node.force_viewport_update, name="Max", default=0)

    def init(self, context):
        # Instead of creating a new mapping, the user can also
        # manipulate an existing mapping
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping (optional)")

        self.outputs.new("LuxCoreSocketMapping2D", "2D Mapping")

    def draw_buttons(self, context, layout):
        # Info about UV mapping so the user can react if no UV map etc.
        utils_node.draw_uv_info(context, layout)

        if "2D Mapping (optional)" in self.inputs:
            input_mapping_node = utils_node.get_linked_node(self.inputs["2D Mapping (optional)"])

            if isinstance(input_mapping_node, LuxCoreNodeTexMapping2D) and input_mapping_node.mapping_type == "uvrandommapping2d":
                layout.label(text="Random not valid as input!", icon=icons.ERROR)
        else:
            input_mapping_node = None

        if not input_mapping_node and context.object:
            layout.prop_search(self, "uvmap", context.object.data, "uv_layers", text="UV Map", icon='GROUP_UVS')

        layout.prop(self, "mapping_type")

        if self.mapping_type == "uvmapping2d":
            layout.prop(self, "center_map")
            layout.prop(self, "use_uniform_scale")

            if self.use_uniform_scale:
                layout.prop(self, "uniform_scale")
            else:
                row = layout.row(align=True)
                row.prop(self, "uscale")
                row.prop(self, "vscale")

            layout.prop(self, "rotation")

            layout.label(text="Offset:")
            row = layout.row(align=True)
            row.prop(self, "udelta")
            row.prop(self, "vdelta")
        elif self.mapping_type == "uvrandommapping2d":
            layout.prop(self, "seed_type")
            if self.seed_type == "object_id":
                layout.prop(self, "object_id_offset")

            box = layout.box()
            col = box.column(align=True)
            col.label(text="Rotation:")
            col.prop(self, "random_rotation_min")
            col.prop(self, "random_rotation_max")

            box = layout.box()
            col = box.column(align=True)
            col.prop(self, "random_uvscale_uniform")
            col.label(text="UV Scale:" if self.random_uvscale_uniform else "U Scale:")
            col.prop(self, "random_uscale_min")
            col.prop(self, "random_uscale_max")
            if not self.random_uvscale_uniform:
                col = box.column(align=True)
                col.label(text="V Scale:")
                col.prop(self, "random_vscale_min")
                col.prop(self, "random_vscale_max")

            box = layout.box()
            col = box.column(align=True)
            col.label(text="U Offset:")
            col.prop(self, "random_udelta_min")
            col.prop(self, "random_udelta_max")
            col = box.column(align=True)
            col.label(text="V Offset:")
            col.prop(self, "random_vdelta_min")
            col.prop(self, "random_vdelta_max")
        else:
            raise NotImplementedError("Unknown uv mapping type:", self.mapping_type)

    def export_uvmapping2d(self, exporter, depsgraph, props):
        input_socket = self.inputs["2D Mapping (optional)"]
        use_fallback = True
        if utils_node.get_link(input_socket):
            definitions = input_socket.export(exporter, depsgraph, props)
            if definitions["mapping.type"] == "uvmapping2d":
                use_fallback = False
                uvindex = definitions["mapping.uvindex"]
                input_uvscale = definitions["mapping.uvscale"]
                input_rotation = definitions["mapping.rotation"]
                input_uvdelta = definitions["mapping.uvdelta"]

        if use_fallback:
            uvindex = self.uvindex
            input_uvscale = [1, -1]
            input_rotation = 0
            input_uvdelta = [0, 0]

        # Scale
        if self.use_uniform_scale:
            uvscale = [self.uniform_scale, self.uniform_scale]
        else:
            uvscale = [self.uscale, self.vscale]
        output_uvscale = [a * b for a, b in zip(input_uvscale, uvscale)]

        # Rotation
        rotation = math.degrees(self.rotation)
        output_rotation = input_rotation + rotation

        # Translation
        if self.center_map:
            uvdelta = [self.udelta + 0.5 * (1 - uvscale[0]),
                       self.vdelta * -1 + 1 - (0.5 * (1 - uvscale[1]))]
        else:
            uvdelta = [self.udelta,
                       self.vdelta + 1]
        output_uvdelta = [a + b for a, b in zip(input_uvdelta, uvdelta)]

        return {
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": output_uvscale,
            "mapping.uvindex": uvindex,
            "mapping.rotation": output_rotation,
            "mapping.uvdelta": output_uvdelta,
        }

    def export_uvrandommapping2d(self):
        definitions = {
            "mapping.type": "uvrandommapping2d",
            "mapping.uvindex": self.uvindex,
            "mapping.rotation": [math.degrees(self.random_rotation_min), math.degrees(self.random_rotation_max)],
            "mapping.uvscale": [self.random_uscale_min, self.random_uscale_max,
                                self.random_vscale_min, self.random_vscale_max],
            "mapping.uvscale.uniform": self.random_uvscale_uniform,
            "mapping.uvdelta": [self.random_udelta_min, self.random_udelta_max,
                                self.random_vdelta_min, self.random_vdelta_max],
        }

        if self.seed_type == "object_id":
            definitions["mapping.seed.type"] = "object_id_offset"
            definitions["mapping.objectidoffset.value"] = self.object_id_offset
        elif self.seed_type == "mesh_islands":
            definitions["mapping.seed.type"] = "triangle_aov"
            definitions["mapping.triangleaov.index"] = TriAOVDataIndices.RANDOM_PER_ISLAND_INT

        return definitions

    def export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        if self.mapping_type == "uvmapping2d":
            return self.export_uvmapping2d(exporter, depsgraph, props)
        elif self.mapping_type == "uvrandommapping2d":
            return self.export_uvrandommapping2d()
        else:
            raise NotImplementedError("Unknown uv mapping type:", self.mapping_type)

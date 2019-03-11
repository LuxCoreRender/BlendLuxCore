import bpy
import mathutils
import math
from time import time
from bpy.props import EnumProperty, PointerProperty, StringProperty
from .. import LuxCoreNodeTexture
from ... import utils
from ...bin import pyluxcore
from ...export import smoke
from ...utils import node as utils_node
from ...ui import icons


class LuxCoreNodeTexSmoke(LuxCoreNodeTexture):
    bl_label = "Smoke"
    bl_width_default = 200

    def poll_domain(self, obj):
        # Only allow objects with a smoke modifier in domain mode to be picked
        return utils.find_smoke_domain_modifier(obj)
    
    domain = PointerProperty(name="Domain", type=bpy.types.Object, poll=poll_domain)

    def update_source(self, context):
        value_output = self.outputs["Value"]
        color_output = self.outputs["Color"]
        was_value_enabled = value_output.enabled

        value_output.enabled = self.source in {"density", "fire", "heat"}
        color_output.enabled = self.source in {"color", "velocity"}

        utils_node.copy_links_after_socket_swap(value_output, color_output, was_value_enabled)

    source_items = [
        ("density", "Density", "Smoke density grid, 1 value per voxel", 0),
        ("fire", "Fire", "Fire grid, 1 value per voxel", 1),
        ("heat", "Heat", "Smoke heat grid, 1 value per voxel", 2),
        ("color", "Color", "Smoke color grid, 3 values per voxel (RGB)", 3),
        ("velocity", "Velocity", "Smoke velocity grid, 3 values per voxel", 4),
    ]
    source = EnumProperty(name="Grid Type", items=source_items, default="density", update=update_source)

    precision_items = [
        ("byte", "Byte", "Only 1 byte per value. Required memory is 1/2 of Half and 1/4 of Float", 0),
        ("half", "Half", "2 bytes per value. Required memory is 1/2 of Float, but 2 times the size of Byte", 1),
        ("float", "Float", "4 bytes per value. Required memory is 2 times the size of half and 4 times the size of Byte", 2),
    ]
    precision = EnumProperty(name="Precision", items=precision_items, default="half",
                             description="How many bytes to use per value. The floating point precision "
                                         "increases/decreases when more/less bytes are used. Low floating "
                                         "point precision can lead to artifacts when the smoke resolution is low")

    def init(self, context):
        self.outputs.new("LuxCoreSocketFloatPositive", "Value")
        color = self.outputs.new("LuxCoreSocketColor", "Color")
        color.enabled = False

    def draw_buttons(self, context, layout):
        layout.prop(self, "domain")

        if self.domain and not utils.find_smoke_domain_modifier(self.domain):
            layout.label("Not a smoke domain!", icon=icons.WARNING)
        elif self.domain is None:
            layout.label("Select the smoke domain object", icon=icons.WARNING)

        col = layout.column()
        col.prop(self, "source")
        col.prop(self, "precision")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        start_time = time()
        print("[Node Tree: %s][Smoke Domain: %s] Beginning smoke export of channel %s"
              % (self.id_data.name, self.domain.name, self.source))

        if not self.domain:
            error = "No Domain object selected."
            msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
            exporter.scene.luxcore.errorlog.add_warning(msg)

            definitions = {
                "type": "constfloat3",
                "value": [0, 0, 0],
            }
            return self.create_props(props, definitions, luxcore_name)

        scale = self.domain.dimensions
        translate = self.domain.matrix_world * mathutils.Vector([v for v in self.domain.bound_box[0]])
        rotate = self.domain.rotation_euler

        # create a location matrix
        tex_loc = mathutils.Matrix.Translation(translate)

        # create an identitiy matrix
        tex_sca = mathutils.Matrix()
        tex_sca[0][0] = scale[0]  # X
        tex_sca[1][1] = scale[1]  # Y
        tex_sca[2][2] = scale[2]  # Z

        # create a rotation matrix
        tex_rot0 = mathutils.Matrix.Rotation(math.radians(rotate[0]), 4, 'X')
        tex_rot1 = mathutils.Matrix.Rotation(math.radians(rotate[1]), 4, 'Y')
        tex_rot2 = mathutils.Matrix.Rotation(math.radians(rotate[2]), 4, 'Z')
        tex_rot = tex_rot0 * tex_rot1 * tex_rot2

        # combine transformations
        mapping_type = 'globalmapping3d'
        matrix_transformation = utils.matrix_to_list(tex_loc * tex_rot * tex_sca,
                                                     scene=exporter.scene,
                                                     apply_worldscale=True,
                                                     invert=True)

        resolution, grid = smoke.convert(self.domain, self.source)
        nx, ny, nz = resolution

        definitions = {
            "type": "densitygrid",
            "wrap": "black",
            "storage": self.precision,
            "nx": nx,
            "ny": ny,
            "nz": nz,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": matrix_transformation,
        }

        luxcore_name = self.create_props(props, definitions, luxcore_name)
        prefix = self.prefix + luxcore_name + "."
        # We use a fast path (AddAllFloat method) here to transfer the grid data to the properties

        if self.source == "color":
            prop = pyluxcore.Property(prefix + "data3", [])
            # Omit every 4th element because the color_grid contains 4 values per cell
            # but LuxCore expects 3 values per cell (r, g, b)
            prop.AddAllFloat(grid, 3, 1)
        elif self.source == "velocity":
            prop = pyluxcore.Property(prefix + "data3", [])
            prop.AddAllFloat(grid)
        else:
            prop = pyluxcore.Property(prefix + "data", [])
            prop.AddAllFloat(grid)

        # We have to free the memory manually because the grid can be VERY large
        # and if we don't invoke the garbage collection, we use way more RAM than necessary
        del grid
        import gc
        gc.collect()

        props.Set(prop)

        elapsed_time = time() - start_time
        print("[Node Tree: %s][Smoke Domain: %s] Smoke export of channel %s took %.3f s"
              % (self.id_data.name, self.domain.name, self.source, elapsed_time))

        return luxcore_name

import bpy
import mathutils
import math
from bpy.props import EnumProperty, PointerProperty, StringProperty
from .. import LuxCoreNodeTexture
from ...export import smoke 
from ...export import caches 
from ... import utils
from .. import LuxCoreNodeTexture


class LuxCoreNodeTexSmoke(LuxCoreNodeTexture):
    bl_label = "Smoke"
    bl_width_min = 200
    
    domain = PointerProperty(name="Domain", type=bpy.types.Object)

    source_items = [
        ("density", "Density", "Smoke density grid"),
        ("fire", "Fire", "Fire grid"),
        ("heat", "Heat", "Smoke heat grid"),
        #ToDo implement velocity export
        #("velocity", "Velocity", "Smoke velocity grid"),
    ]
    source = EnumProperty(name="Source", items=source_items, default="density")

    #ToDo: Descriptions
    wrap_items = [
        ("repeat", "Repeat", "", 0),
        ("clamp", "Clamp", "", 3),
        ("black", "Black", "", 1),
        ("white", "White", "", 2),
    ]
    wrap = EnumProperty(name="Wrap", items=wrap_items, default="black")


    def init(self, context):
        self.outputs.new("LuxCoreSocketFloatPositive", "Float")

    def draw_buttons(self, context, layout):
        layout.prop_search(self, "domain", bpy.data, "objects")
        col = layout.column()
        col.prop(self, "source")
        col.prop(self, "wrap")

    def export(self, props, luxcore_name=None):       
        nx = 1
        ny = 1
        nz = 1
        grid = [1.0]
       
        if self.domain:            
            nx, ny, nz, grid = smoke.convert(self.domain, self.source)
            
            scale = self.domain.dimensions
            translate = self.domain.matrix_world * mathutils.Vector([v for v in self.domain.bound_box[0]])
            rotate = self.domain.rotation_euler
        
            # create a location matrix
            tex_loc = mathutils.Matrix.Translation((translate))
        
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
            matrix_transformation = utils.matrix_to_list(tex_loc * tex_rot * tex_sca, invert=True)
            
        else:
            error = "No Domain object selected."
            msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
            bpy.context.scene.luxcore.errorlog.add_warning(msg)

        definitions = {
            "type": "densitygrid",
            "wrap": self.wrap,
            "nx": nx,
            "ny": ny,
            "nz": nz,
            "data": grid,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": matrix_transformation,
        }

        return self.base_export(props, definitions, luxcore_name)

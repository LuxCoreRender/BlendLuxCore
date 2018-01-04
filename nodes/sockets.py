import mathutils
from bpy.types import NodeSocket
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty

# The rules for socket classes are these:
# - If it is a socket that's used by more than one node, put it in this file
# - If it is only used by one node, put it in the file of that node
#   (e.g. the sigma socket of the matte material)
# Unfortunately we have to create dozens of socket types because there's no other
# way to have different min/max values or different descriptions. However, most of
# the time you only have to overwrite the default_value property of the socket.


ROUGHNESS_DESCRIPTION = "Microfacet roughness; higher values lead to more blurry reflections"
IOR_DESCRIPTION = "Index of refraction; typical values: 1.0 (air), 1.3 (water), 1.5 (glass)"


class LuxCoreNodeSocket(NodeSocket):
    bl_label = ""

    color = (1, 1, 1, 1)
    slider = False

    def draw(self, context, layout, node, text):
        has_default = hasattr(self, "default_value") and self.default_value is not None
        if self.is_output or self.is_linked or not has_default:
            layout.label(text)
        else:
            if type(self.default_value) == mathutils.Color:
                row = layout.row()
                row.alignment = "LEFT"
                row.prop(self, "default_value", text="")
                row.label(text=text)
            else:
                layout.prop(self, "default_value", text=text, slider=self.slider)

    # Socket color
    def draw_color(self, context, node):
        return self.color

    def export_default(self):
        """
        Subclasses have to implement this method.
        It should return the default value in a form ready for a pyluxcore.Property()
        e.g. convert colors to a list
        """
        return None

    def export(self, props, luxcore_name=None):
        if self.is_linked:
            linked_node = self.links[0].from_node
            if luxcore_name:
                return linked_node.export(props, luxcore_name)
            else:
                return linked_node.export(props)
        elif hasattr(self, "default_value"):
            return self.export_default()
        else:
            return None


class Color:
    material = (0.39, 0.78, 0.39, 1.0)
    color_texture = (0.78, 0.78, 0.16, 1.0)
    float_texture = (0.63, 0.63, 0.63, 1.0)
    fresnel_texture = (0.33, 0.6, 0.85, 1.0)
    volume = (1.0, 0.4, 0.216, 1.0)
    mat_emission = (0.9, 0.9, 0.9, 1.0)
    mapping_2d = (0.65, 0.55, 0.75, 1.0)
    mapping_3d = (0.50, 0.25, 0.60, 1.0)


class LuxCoreSocketMaterial(LuxCoreNodeSocket):
    color = Color.material
    # no default value


class LuxCoreSocketVolume(LuxCoreNodeSocket):
    color = Color.volume
    # no default value


class LuxCoreSocketFresnel(LuxCoreNodeSocket):
    color = Color.fresnel_texture
    # no default value


class LuxCoreSocketMatEmission(LuxCoreNodeSocket):
    """ Special socket for material emission """
    color = Color.mat_emission
    # no default value

    def export_emission(self, props, definitions):
        if self.is_linked:
            linked_node = self.links[0].from_node

            if linked_node.bl_idname == "LuxCoreNodeMatEmission":
                linked_node.export(props, definitions)
            else:
                print("ERROR: can't export emission; not an emission node")


class LuxCoreSocketBump(LuxCoreNodeSocket):
    color = Color.float_texture
    # no default value


class LuxCoreSocketColor(LuxCoreNodeSocket):
    color = Color.color_texture
    default_value = FloatVectorProperty(subtype="COLOR", soft_min=0, soft_max=1)

    def export_default(self):
        return list(self.default_value)


class LuxCoreSocketFloat(LuxCoreNodeSocket):
    color = Color.float_texture
    default_value = FloatProperty()

    def export_default(self):
        return self.default_value


class LuxCoreSocketFloatPositive(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0)


class LuxCoreSocketValueAtDepth(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0, subtype='DISTANCE', unit='LENGTH', precision=5)


class LuxCoreSocketFloat0to1(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0, max=1)
    slider = True


class LuxCoreSocketRoughness(LuxCoreSocketFloat):
    # Reflections look weird when roughness gets too small
    default_value = FloatProperty(min=0.001, soft_max=0.8, max=1.0, precision=4, description=ROUGHNESS_DESCRIPTION)
    slider = True


class LuxCoreSocketIOR(LuxCoreSocketFloat):
    default_value = FloatProperty(name="IOR", min=0, soft_max=2.0, max=25, step=0.1, precision=4, description=IOR_DESCRIPTION)

    def draw(self, context, layout, node, text):
        if hasattr(node, "get_interior_volume") and node.get_interior_volume():
            # This socket is used on a glass node and is not exported because
            # the settings of the attached interior volume are used instead.
            layout.active = False

        super().draw(context, layout, node, text)


class LuxCoreSocketFloatVector(LuxCoreSocketFloat):
    default_value = FloatVectorProperty()

    def export_default(self):
        return list(self.default_value)


class LuxCoreSocketMapping2D(LuxCoreNodeSocket):
    color = Color.mapping_2d
    # We have to set the default_value to something
    # so export_default() is called by LuxCoreNodeSocket.export()
    default_value = None

    def export_default(self):
        # These are not the LuxCore API default values because
        # we have to compensate Blenders mirrored V axis
        uvscale = [1, -1]
        uvdelta = [0, 1]
        return uvscale, uvdelta


class LuxCoreSocketMapping3D(LuxCoreNodeSocket):
    color = Color.mapping_3d
    # We have to set the default_value to something
    # so export_default() is called by LuxCoreNodeSocket.export()
    default_value = None

    def export_default(self):
        mapping_type = "globalmapping3d"
        transformation = mathutils.Matrix()
        return mapping_type, transformation

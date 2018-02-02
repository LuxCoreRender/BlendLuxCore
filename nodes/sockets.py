import mathutils
from bpy.types import NodeSocket
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty
from ..utils.node import update_opengl_materials

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
        # Check if the socket linked to this socket is in the set of allowed input socket classes.
        if self.is_linked and hasattr(self, "allowed_inputs"):
            is_allowed = False
            for allowed_class in self.allowed_inputs:
                if isinstance(self.links[0].from_socket, allowed_class):
                    is_allowed = True
                    break

            if not is_allowed:
                layout.label("Wrong Input!", icon="CANCEL")
                return

        has_default = hasattr(self, "default_value") and self.default_value is not None

        if self.is_output or self.is_linked or not has_default:
            layout.label(text)

            # Show a button that lets the user add a node for this socket instantly.
            # Sockets that only accept one node (e.g. volume, emission, fresnel) should have a default_node member
            show_operator = not self.is_output and not self.is_linked and hasattr(self, "default_node")
            # Don't show for volume sockets on volume output
            is_vol_socket_on_vol_output = self.bl_idname == "LuxCoreSocketVolume" and node.bl_idname == "LuxCoreNodeVolOutput"

            if show_operator and not is_vol_socket_on_vol_output:
                op = layout.operator("luxcore.add_node", icon="ZOOMIN")
                op.node_type = self.default_node
                op.socket_type = self.bl_idname
                op.input_socket = self.name
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
    # The node type that can be instantly added to this node
    # (via operator drawn in LuxCoreNodeSocket)
    default_node = "LuxCoreNodeTreePointer"
    # no default value


class LuxCoreSocketFresnel(LuxCoreNodeSocket):
    color = Color.fresnel_texture
    # The node type that can be instantly added to this node
    # (via operator drawn in LuxCoreNodeSocket)
    default_node = "LuxCoreNodeTexFresnel"
    # no default value


class LuxCoreSocketMatEmission(LuxCoreNodeSocket):
    """ Special socket for material emission """
    color = Color.mat_emission
    # The node type that can be instantly added to this node
    # (via operator drawn in LuxCoreNodeSocket)
    default_node = "LuxCoreNodeMatEmission"
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
    # Currently this is the only socket that updates OpenGL materials
    default_value = FloatVectorProperty(subtype="COLOR", soft_min=0, soft_max=1,
                                        update=update_opengl_materials)

    def export_default(self):
        return list(self.default_value)


# Warning! For some reason unknown to me, you can't use this socket on any node!
# Use the "LuxCoreSocketFloatUnbounded" class below instead.
class LuxCoreSocketFloat(LuxCoreNodeSocket):
    color = Color.float_texture
    default_value = FloatProperty()

    def export_default(self):
        return self.default_value


# Use this socket for normal float values without min/max bounds.
# For some unkown reason, we can't use the LuxCoreSocketFloat directly.
class LuxCoreSocketFloatUnbounded(LuxCoreSocketFloat):
    default_value = FloatProperty(description="Float value")


class LuxCoreSocketFloatPositive(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0, description="Positive float value")


class LuxCoreSocketFloat0to1(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0, max=1, description="Float value between 0 and 1")
    slider = True


class LuxCoreSocketFloat0to2(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0, max=2, description="Float value between 0 and 2")
    slider = True


class LuxCoreSocketRoughness(LuxCoreSocketFloat):
    # Reflections look weird when roughness gets too small
    default_value = FloatProperty(min=0.001, soft_max=0.8, max=1.0, precision=4,
                                  description=ROUGHNESS_DESCRIPTION)
    slider = True


class LuxCoreSocketIOR(LuxCoreSocketFloat):
    default_value = FloatProperty(name="IOR", min=0, soft_max=2.0, max=25, step=0.1,
                                  precision=4, description=IOR_DESCRIPTION)

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


# Specify the allowed inputs of sockets. Subclasses inherit the settings of their parents.
# We have to do this here because some sockets (e.g. Material) need to refer to their own class.
LuxCoreSocketMaterial.allowed_inputs = {LuxCoreSocketMaterial}
LuxCoreSocketVolume.allowed_inputs = {LuxCoreSocketVolume}
LuxCoreSocketFresnel.allowed_inputs = {LuxCoreSocketFresnel}
LuxCoreSocketMatEmission.allowed_inputs = {LuxCoreSocketMatEmission}
LuxCoreSocketBump.allowed_inputs = {LuxCoreSocketBump, LuxCoreSocketColor, LuxCoreSocketFloat}
LuxCoreSocketColor.allowed_inputs = {LuxCoreSocketColor, LuxCoreSocketFloat}
LuxCoreSocketFloat.allowed_inputs = {LuxCoreSocketColor, LuxCoreSocketFloat}
LuxCoreSocketMapping2D.allowed_inputs = {LuxCoreSocketMapping2D}
LuxCoreSocketMapping3D.allowed_inputs = {LuxCoreSocketMapping3D}

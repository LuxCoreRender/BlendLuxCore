import mathutils
from bpy.types import NodeSocket
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, BoolProperty
from ..utils.node import update_opengl_materials
from ..ui import icons

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

    def draw_prop(self, context, layout, node, text):
        """
        This method can be overriden by subclasses to draw their property differently
        (e.g. done by LuxCoreSocketColor)
        """
        layout.prop(self, "default_value", text=text, slider=self.slider)

    def draw(self, context, layout, node, text):
        # Check if the socket linked to this socket is in the set of allowed input socket classes.
        link = self._get_link()

        if link and hasattr(self, "allowed_inputs"):
            is_allowed = False

            for allowed_class in self.allowed_inputs:
                if isinstance(link.from_socket, allowed_class):
                    is_allowed = True
                    break

            if not is_allowed:
                layout.label("Wrong Input!", icon=icons.ERROR)
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
                op = layout.operator("luxcore.add_node", icon=icons.ADD)
                op.node_type = self.default_node
                op.socket_type = self.bl_idname
                op.input_socket = self.name
        else:
            self.draw_prop(context, layout, node, text)

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

    def export(self, exporter, props, luxcore_name=None):
        link = self._get_link()

        if link:
            return link.from_node.export(exporter, props, luxcore_name, link.from_socket)
        elif hasattr(self, "default_value"):
            return self.export_default()
        else:
            return None

    def _get_link(self):
        """
        Returns the link if this socket is linked, None otherwise.
        All reroute nodes between this socket and the next non-reroute node are skipped.
        """

        if self.is_linked:
            link = self.links[0]

            while link.from_node.bl_idname == "NodeReroute":
                if link.from_node.inputs[0].is_linked:
                    link = link.from_node.inputs[0].links[0]
                else:
                    # If the left-most reroute has no input, it is like self.is_linked == False
                    return None

            return link
        else:
            return None


class Color:
    material = (0.39, 0.78, 0.39, 1.0)
    color_texture = (0.78, 0.78, 0.16, 1.0)
    float_texture = (0.63, 0.63, 0.63, 1.0)
    vector_texture = (0.39, 0.39, 0.78, 1.0)
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

    def export_emission(self, exporter, props, definitions):
        if self.is_linked:
            linked_node = self.links[0].from_node

            if linked_node.bl_idname == "LuxCoreNodeMatEmission":
                linked_node.export_emission(exporter, props, definitions)
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

    def draw_prop(self, context, layout, node, text):
        row = layout.row()
        row.alignment = "LEFT"
        row.prop(self, "default_value", text="")
        row.label(text=text)

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


class LuxCoreSocketVector(LuxCoreNodeSocket):
    color = Color.vector_texture
    default_value = FloatVectorProperty(name="", subtype="XYZ", precision=3)
    expand = BoolProperty(default=False)

    def draw_prop(self, context, layout, node, text):
        split = layout.split(percentage=0.1)

        col = split.column()
        icon = icons.EXPANDABLE_OPENED if self.expand else icons.EXPANDABLE_CLOSED
        col.prop(self, "expand", text="", icon=icon)

        if self.expand:
            split = split.split(percentage=0.6)
            col = split.column()
            col.prop(self, "default_value", expand=True)

        col = split.column()
        if self.expand:
            # Empty label to center the text vertically
            col.label("")
        else:
            # Show the value of the vector even in collapsed form
            text += " (%s)" % (", ".join(str(round(x, 2)) for x in self.default_value))
        col.label(text)

    def export_default(self):
        return list(self.default_value)


class LuxCoreSocketRoughness(LuxCoreSocketFloat):
    # Reflections look weird when roughness gets too small
    default_value = FloatProperty(min=0.001, soft_max=0.8, max=1.0, precision=4,
                                  description=ROUGHNESS_DESCRIPTION)
    slider = True


class LuxCoreSocketIOR(LuxCoreSocketFloat):
    default_value = FloatProperty(name="IOR", min=1, soft_max=2.0, max=25, step=0.1,
                                  precision=4, description=IOR_DESCRIPTION)

    def draw(self, context, layout, node, text):
        if hasattr(node, "get_interior_volume") and node.get_interior_volume():
            # This socket is used on a glass node and is not exported because
            # the settings of the attached interior volume are used instead.
            layout.active = False

        super().draw(context, layout, node, text)


class LuxCoreSocketVolumeAsymmetry(LuxCoreNodeSocket):
    color = Color.vector_texture
    default_value = FloatVectorProperty(name="", default=(0, 0, 0), min=-1, max=1, subtype="COLOR",
                                        description="Scattering asymmetry. -1 means back scatter, "
                                                    "0 is isotropic, 1 is forwards scattering")

    def draw_prop(self, context, layout, node, text):
        split = layout.split()
        col = split.column()
        # Empty label to center the text vertically
        col.label("")
        col.label("Asymmetry:")

        col = split.column()
        col.prop(self, "default_value", expand=True)

    def export_default(self):
        return list(self.default_value)


class LuxCoreSocketMapping2D(LuxCoreNodeSocket):
    color = Color.mapping_2d
    # The node type that can be instantly added to this node
    # (via operator drawn in LuxCoreNodeSocket)
    default_node = "LuxCoreNodeTexMapping2D"
    # We have to set the default_value to something
    # so export_default() is called by LuxCoreNodeSocket.export()
    default_value = None

    def export_default(self):
        # These are not the LuxCore API default values because
        # we have to compensate Blenders mirrored V axis
        uvscale = [1, -1]
        uvrotation = 0
        uvdelta = [0, 1]
        return uvscale, uvrotation, uvdelta


class LuxCoreSocketMapping3D(LuxCoreNodeSocket):
    color = Color.mapping_3d
    # The node type that can be instantly added to this node
    # (via operator drawn in LuxCoreNodeSocket)
    default_node = "LuxCoreNodeTexMapping3D"
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
LuxCoreSocketColor.allowed_inputs = {LuxCoreSocketColor, LuxCoreSocketFloat, LuxCoreSocketVector}
# Note: Utility nodes like "math" can be used to add bumpmaps together, so we allow Bump input here
LuxCoreSocketFloat.allowed_inputs = {LuxCoreSocketColor, LuxCoreSocketFloat, LuxCoreSocketBump}
LuxCoreSocketVector.allowed_inputs = {LuxCoreSocketVector, LuxCoreSocketColor, LuxCoreSocketFloat}
LuxCoreSocketMapping2D.allowed_inputs = {LuxCoreSocketMapping2D}
LuxCoreSocketMapping3D.allowed_inputs = {LuxCoreSocketMapping3D}

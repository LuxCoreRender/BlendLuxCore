import bpy
import mathutils
import pyluxcore
from .errorlog import LuxCoreErrorLog
from ..ui import icons


def draw_uv_info(context, layout):
    """
    Call this function on nodes that use UV mapping (e.g. the Roughness class uses it
    when anisotropic roughness is enabled because it requires UV mapping).
    """
    obj = context.object

    def warning_no_uvmap(_layout):
        _layout.label(text="No UV map", icon=icons.WARNING)

    if obj and obj.data:
        if obj.type in {"CURVE", "SURFACE", "FONT"}:
            # These data types always have UVs
            pass
        elif obj.type == "MESH":
            if len(obj.data.uv_layers) == 0:
                row = layout.row()
                warning_no_uvmap(row)
                row.operator("mesh.uv_texture_add")
        else:
            warning_no_uvmap(layout)


def has_valid_uv_map(obj):
    if not obj.data:
        return False

    if obj.type == "MESH" and len(obj.data.uv_layers) == 0:
        return False

    return True


def draw_transmission_info(node, layout):
    try:
        kd_socket = node.inputs["Diffuse Color"]
    except KeyError:
        # For some reason, this socket is named differently in the mattetranslucent material
        kd_socket = node.inputs["Reflection Color"]

    kt_socket = node.inputs["Transmission Color"]

    if not kd_socket.is_linked and not kt_socket.is_linked:
        # V component of the HSV color model
        kd_value = kd_socket.default_value.v
        kt_value = kt_socket.default_value.v
        # Note that this is an estimation.
        # We are for example not accounting for specular reflections
        transmitted = min(1 - kd_value, kt_value)
        layout.label(text="Transmitted: %.2f" % transmitted, icon=icons.INFO)


def export_material_input(input, exporter, depsgraph, props, luxcore_name=None):
    material_name = input.export(exporter, depsgraph, props, luxcore_name)

    if material_name:
        return material_name
    else:
        LuxCoreErrorLog.add_warning(f"WARNING: No material linked on input {input.name} of node {input.node.name}")
        if luxcore_name is None:
            luxcore_name = "__BLACK__"
        props.Set(pyluxcore.Property("scene.materials.%s.type" % luxcore_name, "matte"))
        props.Set(pyluxcore.Property("scene.materials.%s.kd" % luxcore_name, [0, 0, 0]))
        return luxcore_name


def get_link(socket):
    """
    Returns the link if this socket is linked, None otherwise.
    All reroute nodes between this socket and the next non-reroute node are skipped.
    Muted nodes are ignored.
    """

    if not socket.is_linked:
        return None
    
    if len(socket.links) < 1:
        return None

    link = socket.links[0]

    while link.from_node.bl_idname == "NodeReroute" or link.from_node.mute:
        node = link.from_node

        if node.mute:
            if node.internal_links:
                # Only nodes defined in C can have internal_links in Blender
                links = node.internal_links[0].from_socket.links
                if links:
                    link = links[0]
                else:
                    return None
            else:
                if not link.from_socket.bl_idname.startswith("LuxCoreSocket") or not node.inputs:
                    return None

                # We can't define internal_links, so try to make up a link that makes sense.
                found_internal_link = False

                for input_socket in node.inputs:
                    if input_socket.links and link.from_socket.is_allowed_input(input_socket):
                        link = input_socket.links[0]
                        found_internal_link = True
                        break

                if not found_internal_link:
                    return None
        else:
            # Reroute node
            if node.inputs[0].is_linked:
                link = node.inputs[0].links[0]
            else:
                # If the left-most reroute has no input, it is like self.is_linked == False
                return None

    return link


def get_linked_node(socket):
    """
    Returns the connected node if this socket is linked, None otherwise.
    All reroute nodes between this socket and the next non-reroute node are skipped.
    """
    link = get_link(socket)
    if not link:
        return None
    return link.from_node


def find_nodes(node_tree, bl_idname, follow_pointers):
    result = []

    for node in node_tree.nodes:
        if follow_pointers and node.bl_idname == "LuxCoreNodeTreePointer" and node.node_tree:
            try:
                result += find_nodes(node.node_tree, bl_idname, follow_pointers)
            except RecursionError:
                msg = (f'Pointer nodes in node trees "{node_tree.name}" and "{node.node_tree.name}" '
                       "create a dependency cycle! Delete one of them.")
                LuxCoreErrorLog.add_error(msg)
                # Mark the faulty nodes in red
                node.use_custom_color = True
                node.color = (0.9, 0, 0)
                return result
        if node.bl_idname == bl_idname:
            result.append(node)

    return result


def find_nodes_multi(node_tree, bl_idname_set, follow_pointers):
    result = []

    for node in node_tree.nodes:
        if follow_pointers and node.bl_idname == "LuxCoreNodeTreePointer" and node.node_tree:
            try:
                result += find_nodes_multi(node.node_tree, bl_idname_set, follow_pointers)
            except RecursionError:
                msg = (f'Pointer nodes in node trees "{node_tree.name}" and "{node.node_tree.name}" '
                       "create a dependency cycle! Delete one of them.")
                LuxCoreErrorLog.add_error(msg)
                # Mark the faulty nodes in red
                node.use_custom_color = True
                node.color = (0.9, 0, 0)
                return result
        if node.bl_idname in bl_idname_set:
            result.append(node)

    return result


def has_nodes(node_tree, bl_idname, follow_pointers):
    for node in node_tree.nodes:
        if follow_pointers and node.bl_idname == "LuxCoreNodeTreePointer" and node.node_tree:
            try:
                if has_nodes(node.node_tree, bl_idname, follow_pointers):
                    return True
            except RecursionError:
                msg = (f'Pointer nodes in node trees "{node_tree.name}" and "{node.node_tree.name}" '
                       "create a dependency cycle! Delete one of them.")
                LuxCoreErrorLog.add_error(msg)
                # Mark the faulty nodes in red
                node.use_custom_color = True
                node.color = (0.9, 0, 0)
                return False
        if node.bl_idname == bl_idname:
            return True

    return False


def has_nodes_multi(node_tree, bl_idname_set, follow_pointers):
    for node in node_tree.nodes:
        if follow_pointers and node.bl_idname == "LuxCoreNodeTreePointer" and node.node_tree:
            try:
                if has_nodes_multi(node.node_tree, bl_idname_set, follow_pointers):
                    return True
            except RecursionError:
                msg = (f'Pointer nodes in node trees "{node_tree.name}" and "{node.node_tree.name}" '
                       "create a dependency cycle! Delete one of them.")
                LuxCoreErrorLog.add_error(msg)
                # Mark the faulty nodes in red
                node.use_custom_color = True
                node.color = (0.9, 0, 0)
                return False
        if node.bl_idname in bl_idname_set:
            return True

    return False


def force_viewport_update(_, context):
    """
    Since Blender 2.80, properties on custom sockets and custom nodes are not listed
    in the depsgraph updates. This function is a workaround to flag the material as
    updated, so we can update it during viewport render.
    Corresponding bug report: https://developer.blender.org/T66521
    """
    if not getattr(context, "object", None) or not getattr(context.object, "active_material", None):
        return
    mat = context.object.active_material
    mat.diffuse_color = mat.diffuse_color


def force_viewport_mesh_update(_, context):
    """ For updates on shape modifier changes (displacement, simplify etc.) """
    # TODO ensure shape update on input texture changes. Need to evaluate the node tree ...
    # TODO ensure shape update on socket connection changes
    mat = context.object.active_material
    for obj in context.visible_objects:
        for slot in obj.material_slots:
            if slot.material == mat:
                if obj.data:
                    obj.data.update_tag()
                    break


def force_viewport_mesh_update2(node_tree):
    for obj in bpy.data.objects:
        for slot in obj.material_slots:
            if slot.material.luxcore.node_tree == node_tree:
                if obj.data:
                    obj.data.update_tag()
                    break


def update_opengl_materials(_, context):
    if (not hasattr(context, "object")
            or not context.object
            or not context.object.active_material
            or not context.object.active_material.luxcore.auto_vp_color):
        return

    mat = context.object.active_material
    node_tree = mat.luxcore.node_tree
    diffuse_color = (0, 0, 0)
    alpha = 1

    if node_tree is None:
        mat.diffuse_color = (0.5, 0.5, 0.5, alpha)
        return

    from ..nodes.output import get_active_output
    output = get_active_output(node_tree)

    if output:
        first_node = get_linked_node(output.inputs["Material"])

        if first_node:
            # Set default color for nodes without color sockets, e.g. mix or glossy coating
            diffuse_color = (0.5, 0.5, 0.5)

            if first_node.inputs:
                # Usually we want to show the color in the first input as main color
                socket = first_node.inputs[0]
                socket_value = getattr(socket, "default_value", None)

                if not socket.is_linked and isinstance(socket_value, mathutils.Color):
                    diffuse_color = socket_value

                if "Opacity" in first_node.inputs:
                    socket = first_node.inputs["Opacity"]
                    if not socket.is_linked:
                        alpha = socket.default_value

    mat.diffuse_color = (*diffuse_color, alpha)


def copy_links_after_socket_swap(socket1, socket2, was_socket1_enabled):
    """
    Copy socket links from the output socket that was disabled to the one that was enabled.
    This function should be used on nodes that have two different output sockets which are
    enabled or disabled in turn depending on settings of the node.
    Example: the smoke node (color output when color grid is selected, value output otherwise).
    """
    node_tree = socket1.id_data
    if was_socket1_enabled == socket1.enabled:
        # Nothing changed
        pass
    elif was_socket1_enabled and not socket1.enabled:
        # socket1 was disabled while socket2 was enabled
        for link in socket1.links:
            node_tree.links.new(socket2, link.to_socket)
    else:
        # socket2 was disabled while socket1 was enabled
        for link in socket2.links:
            node_tree.links.new(socket1, link.to_socket)


def get_links(node_tree, socket):
    """List of node links from or to this socket"""
    return tuple(link for link in node_tree.links
                 if (link.from_socket == socket or
                     link.to_socket == socket))


def is_allowed_input(socket, input_socket):
    if not hasattr(socket, "allowed_inputs"):
        return True
    for allowed_class in socket.allowed_inputs:
        if isinstance(input_socket, allowed_class):
            return True
    return False

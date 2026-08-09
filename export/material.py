import bpy
import pyluxcore
from .. import utils
from ..utils import node as utils_node
from ..utils.node import get_active_output
from ..utils.errorlog import LuxCoreErrorLog
from . import cycles_node_reader


GLOBAL_FALLBACK_MAT = "__CLAY__"

is_blender_5 = bpy.app.version[0] >= 5 # only test of Blender 5 for now

def convert(exporter, depsgraph, material, is_viewport_render, obj_name="", force_holdout=False):
    try:
        if material is None:
            return fallback()

        props = pyluxcore.Properties()
        luxcore_name = utils.get_luxcore_name(material, is_viewport_render)

        # If force_holdout, append suffix to create variant material
        if force_holdout:
            luxcore_name += "_holdout"
        node_tree = material.luxcore.node_tree

        # Try to use Cycles nodes on assets without LuxCore nodes, so the user doesn't have to 
        # open all asset files individually and enable use_cycles_nodes everywhere by hand or script
        is_asset_without_lux_mat = node_tree is None and material.library
        
        if is_blender_5:
            # material.use_nodes is deprecated in Blender 5.0.
            # Technically still OK to use for now but made explicit by this.
            matusenodes = True
        else:
            matusenodes = material.use_nodes

        if matusenodes and (material.luxcore.use_cycles_nodes or is_asset_without_lux_mat):
            return cycles_node_reader.convert(material, props, luxcore_name, obj_name, force_holdout)

        if node_tree is None:
            LuxCoreErrorLog.add_warning(f'Material "{material.name}": Missing node tree', obj_name=obj_name)
            return fallback(luxcore_name, force_holdout)

        active_output = get_active_output(node_tree)

        if active_output is None:
            LuxCoreErrorLog.add_warning(f'Node tree "{node_tree.name}": Missing active output node', obj_name=obj_name)
            return fallback(luxcore_name, force_holdout)

        if _has_volumes_and_transparency(node_tree, active_output):
            msg = f'Material "{material.name}": Combining volumes and materials with opacity < 1 can lead to artifacts!'
            LuxCoreErrorLog.add_warning(msg, obj_name=obj_name)

        # Now export the material node tree, starting at the output node
        active_output.export(exporter, depsgraph, props, luxcore_name)

        # Override: If force_holdout, set holdout.enable flag
        # Similar to how Cycles respects LayerCollection.holdout
        if force_holdout:
            import sys
            sys.stderr.write(f"[MAT HOLDOUT] Setting holdout for {luxcore_name}\n")
            sys.stderr.flush()
            prefix = "scene.materials." + luxcore_name + "."
            props.Set(pyluxcore.Property(prefix + "holdout.enable", True))
            sys.stderr.write(f"[MAT HOLDOUT] Props after Set: {props.GetSize()}\n")
            sys.stderr.flush()

        return luxcore_name, props
    except Exception as error:
        msg = f'Material "{material.name}": {error}'
        LuxCoreErrorLog.add_warning(msg, obj_name=obj_name)
        import traceback
        traceback.print_exc()
        return fallback()


def fallback(luxcore_name=GLOBAL_FALLBACK_MAT, force_holdout=False):
    props = pyluxcore.Properties()

    if force_holdout:
        # If holdout is forced, create holdout material instead of matte
        luxcore_name_with_suffix = luxcore_name if luxcore_name == GLOBAL_FALLBACK_MAT else luxcore_name + "_holdout"
        props.SetFromString("""
        scene.materials.{mat_name}.type = matte
        scene.materials.{mat_name}.kd = 0.5
        scene.materials.{mat_name}.holdout.enable = true
        """.format(mat_name=luxcore_name_with_suffix))
        return luxcore_name_with_suffix, props
    else:
        props.SetFromString("""
        scene.materials.{mat_name}.type = matte
        scene.materials.{mat_name}.kd = 0.5
        """.format(mat_name=luxcore_name))
        return luxcore_name, props


def _has_volumes_and_transparency(node_tree, active_output):
    if (utils_node.get_linked_node(active_output.inputs["Interior Volume"])
            or utils_node.get_linked_node(active_output.inputs["Exterior Volume"])):
        for node in node_tree.nodes:
            if "Opacity" in node.inputs:
                opacity_socket = node.inputs["Opacity"]
                if opacity_socket.is_linked or opacity_socket.default_value < 1:
                    return True
    return False

from ..bin import pyluxcore
from .. import utils
from ..nodes.output import get_active_output
from ..utils.errorlog import LuxCoreErrorLog
from . import cycles_node_reader


GLOBAL_FALLBACK_MAT = "__CLAY__"


def convert(exporter, depsgraph, material, is_viewport_render, obj_name=""):
    try:
        if material is None:
            return fallback()

        props = pyluxcore.Properties()
        luxcore_name = utils.get_luxcore_name(material, is_viewport_render)
        node_tree = material.luxcore.node_tree

        # Try to use Cycles nodes on assets without LuxCore nodes, so the user doesn't have to 
        # open all asset files individually and enable use_cycles_nodes everywhere by hand or script
        is_asset_without_lux_mat = node_tree is None and material.library
        
        if material.use_nodes and (material.luxcore.use_cycles_nodes or is_asset_without_lux_mat):
            return cycles_node_reader.convert(material, props, luxcore_name, obj_name)

        if node_tree is None:
            msg = 'Material "%s": Missing node tree' % material.name
            LuxCoreErrorLog.add_warning(msg, obj_name=obj_name)
            return fallback(luxcore_name)

        active_output = get_active_output(node_tree)

        if active_output is None:
            msg = 'Node tree "%s": Missing active output node' % node_tree.name
            LuxCoreErrorLog.add_warning(msg, obj_name=obj_name)
            return fallback(luxcore_name)

        # Now export the material node tree, starting at the output node
        active_output.export(exporter, depsgraph, props, luxcore_name)

        return luxcore_name, props
    except Exception as error:
        msg = 'Material "%s": %s' % (material.name, error)
        LuxCoreErrorLog.add_warning(msg, obj_name=obj_name)
        import traceback
        traceback.print_exc()
        return fallback()


def fallback(luxcore_name=GLOBAL_FALLBACK_MAT):
    props = pyluxcore.Properties()
    props.SetFromString("""
    scene.materials.{mat_name}.type = matte
    scene.materials.{mat_name}.kd = 0.5
    """.format(mat_name=luxcore_name))
    return luxcore_name, props

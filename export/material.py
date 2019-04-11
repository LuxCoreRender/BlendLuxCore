from ..bin import pyluxcore
from .. import utils
from ..nodes.output import get_active_output


GLOBAL_FALLBACK_MAT = "__CLAY__"


def convert(exporter, material, scene, context, obj_name=""):
    try:
        if material is None:
            return fallback()

        props = pyluxcore.Properties()
        luxcore_name = utils.get_luxcore_name(material, context)

        node_tree = material.luxcore.node_tree
        if node_tree is None:
            msg = 'Material "%s": Missing node tree' % material.name
            scene.luxcore.errorlog.add_warning(msg, obj_name=obj_name)
            return fallback(luxcore_name)

        active_output = get_active_output(node_tree)

        if active_output is None:
            msg = 'Node tree "%s": Missing active output node' % node_tree.name
            scene.luxcore.errorlog.add_warning(msg, obj_name=obj_name)
            return fallback(luxcore_name)

        # Now export the material node tree, starting at the output node
        active_output.export(exporter, props, luxcore_name)

        return luxcore_name, props
    except Exception as error:
        msg = 'Material "%s": %s' % (material.name, error)
        scene.luxcore.errorlog.add_warning(msg, obj_name=obj_name)
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

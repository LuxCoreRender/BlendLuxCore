from ..bin import pyluxcore
from .. import utils
from ..nodes.output import get_active_output


GLOBAL_FALLBACK_MAT = "__CLAY__"


def convert(material, scene):
    try:
        if material is None:
            return fallback()

        # print("converting material:", material.name)
        props = pyluxcore.Properties()
        luxcore_name = utils.get_unique_luxcore_name(material)

        node_tree = material.luxcore.node_tree
        if node_tree is None:
            msg = 'Material "%s": Missing node tree' % material.name
            scene.luxcore.errorlog.add_warning(msg)
            return fallback(luxcore_name)

        active_output = get_active_output(node_tree)

        if active_output is None:
            msg = 'Node tree "%s": Missing active output node' % node_tree.name
            scene.luxcore.errorlog.add_warning(msg)
            return fallback(luxcore_name)

        # Now export the material node tree, starting at the output node
        active_output.export(props, luxcore_name)

        return luxcore_name, props
    except Exception as error:
        msg = 'Material "%s": %s' % (material.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()
        return fallback()


def fallback(luxcore_name=GLOBAL_FALLBACK_MAT):
    props = pyluxcore.Properties()
    props.Set(pyluxcore.Property("scene.materials.%s.type" % luxcore_name, "matte"))
    props.Set(pyluxcore.Property("scene.materials.%s.kd" % luxcore_name, [0.5] * 3))
    return luxcore_name, props

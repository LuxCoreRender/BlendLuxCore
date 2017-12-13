from ..bin import pyluxcore
from .. import utils


GLOBAL_FALLBACK_MAT = "__CLAY__"


def convert(material):
    try:
        # print("converting material:", material.name)
        props = pyluxcore.Properties()
        luxcore_name = utils.get_unique_luxcore_name(material)

        node_tree = material.luxcore.node_tree
        if node_tree is None:
            print('ERROR: No node tree found in material "%s"' % material.name)
            return fallback(luxcore_name)

        active_output = None
        for node in node_tree.nodes:
            node_type = getattr(node, "bl_idname", None)

            if node_type == "LuxCoreNodeMatOutput" and node.active:
                active_output = node
                break

        if active_output is None:
            print('ERROR: No active output node found in nodetree "%s"' % node_tree.name)
            return fallback(luxcore_name)

        active_output.export(props, luxcore_name)
        return luxcore_name, props
    except Exception as error:
        # TODO: collect exporter errors
        print("ERROR in material", material.name)
        print(error)
        return fallback()


def fallback(luxcore_name=GLOBAL_FALLBACK_MAT):
    props = pyluxcore.Properties()
    props.Set(pyluxcore.Property("scene.materials.%s.type" % luxcore_name, "matte"))
    props.Set(pyluxcore.Property("scene.materials.%s.kd" % luxcore_name, [0.7, 0.7, 0.7]))
    return luxcore_name, props

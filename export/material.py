from ..bin import pyluxcore
from .. import utils

def convert(material):
    print("converting object:", material.name)
    props = pyluxcore.Properties()

    node_tree = material.luxcore.node_tree
    if node_tree is None:
        print("ERROR: No node tree found in material", material.name)
        return _fallback()

    active_output = None
    for node in node_tree.nodes:
        node_type = getattr(node, "bl_idname", None)

        if node_type == "luxcore_material_output" and node.active:
            active_output = node
            break

    if active_output is None:
        print("ERROR: No active output node found in nodetree", node_tree.name)
        return _fallback()

    luxcore_name = active_output.export(props)
    return luxcore_name, props

def _fallback():
    props = pyluxcore.Properties()
    props.Set(pyluxcore.Property("scene.materials.__CLAY__.type", "matte"))
    props.Set(pyluxcore.Property("scene.materials.__CLAY__.kd", [0.7, 0.7, 0.7]))
    return "__CLAY__", props
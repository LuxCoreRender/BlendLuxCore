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
            # Node tree is attached to object as fallback for now because of Blender bug.
            # This only allows to have one material per object.
            # TODO: waiting for a fix: https://developer.blender.org/T53509
            import bpy
            for obj in bpy.data.objects:
                if len(obj.material_slots) > 0:
                    mat = obj.material_slots[0].material
                    if mat == material:
                        # We found an object with this material - let's hope it has a link to the right node tree
                        node_tree = obj.luxcore.node_tree
                        print("Using fallback node tree on object", obj.name)
                        break

            # TODO remove "if node_tree is None" once code above is not needed anymore
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

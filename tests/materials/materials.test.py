import unittest

import BlendLuxCore
from BlendLuxCore.bin import pyluxcore
from BlendLuxCore import utils
from BlendLuxCore.nodes.output import get_active_output
import bpy


def assertListsAlmostEqual(test_case, list1, list2, places=3):
    test_case.assertEqual(len(list1), len(list2))

    for i in range(len(list1)):
        test_case.assertAlmostEqual(list1[i], list2[i], places=places)

def assertAlmostEqual(test_case, value1, value2, places=3):
    # Try to unpack the value if it is a list with only one element (common for LuxCore props)
    if isinstance(value1, list) and isinstance(value2, list):
        test_case.assertEqual(len(value1), 1)
        test_case.assertEqual(len(value1), len(value2))
        test_case.assertAlmostEqual(value1[0], value2[0], places=places)
    else:
        test_case.assertAlmostEqual(value1, value2, places=places)


def export_first_mat(type_str):
    """
    Export material node tree on material slot 0.
    type_str is the name of the object with the material to export, e.g. "matte"
    """
    obj = bpy.data.objects[type_str]
    mat = obj.material_slots[0].material
    node_tree = mat.luxcore.node_tree
    active_output = get_active_output(node_tree)

    luxcore_name = utils.get_unique_luxcore_name(mat)
    props = pyluxcore.Properties()

    # Now export the material node tree, starting at the output node
    active_output.export(props, luxcore_name)
    prefix = "scene.materials." + luxcore_name

    return props, luxcore_name, prefix


class TestMaterials(unittest.TestCase):
    def test_matte(self):
        props, luxcore_name, prefix = export_first_mat("matte")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["roughmatte"])
        assertListsAlmostEqual(self, props.Get(prefix + ".kd").Get(), [0.5, 0.0, 0.0])
        assertAlmostEqual(self, props.Get(prefix + ".sigma").Get(), [0.2])

    def test_mix(self):
        props, luxcore_name, prefix = export_first_mat("mix")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["mix"])
        assertAlmostEqual(self, props.Get(prefix + ".amount").Get(), [0.3])

        # TODO check if the mixed materials were exported correctly
        # obj = bpy.data.objects["mix"]
        # mat = obj.material_slots[0].material
        # node_tree = mat.luxcore.node_tree
        # active_output = get_active_output(node_tree)
        # mix_node = active_output.inputs["Material"].links[0].from_node
        # mat1_node = mix_node.inputs["Material 1"].links[0].from_node
        # mat2_node = mix_node.inputs["Material 2"].links[0].from_node
        # ...

    def test_mattetranslucent(self):
        props, luxcore_name, prefix = export_first_mat("mattetranslucent")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["mattetranslucent"])
        assertListsAlmostEqual(self, props.Get(prefix + ".kr").Get(), [0.5, 0.0, 0.0])
        assertListsAlmostEqual(self, props.Get(prefix + ".kt").Get(), [0.5, 0.0, 0.0])

    def test_metal(self):
        props, luxcore_name, prefix = export_first_mat("metal")

        # Only one texture in the props (the helper)
        all_exported_tex_prefixes = props.GetAllUniqueSubNames("scene.textures")
        helper_prefix = all_exported_tex_prefixes[0]

        self.assertEqual(props.Get(prefix + ".type").Get(), ["metal2"])
        self.assertEqual(props.Get(prefix + ".fresnel").Get(), [helper_prefix.split(".")[-1]])
        assertAlmostEqual(self, props.Get(prefix + ".uroughness").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".vroughness").Get(), [0.1])

        self.assertEqual(props.Get(helper_prefix + ".type").Get(), ["fresnelcolor"])
        assertListsAlmostEqual(self, props.Get(helper_prefix + ".kr").Get(), [0.5, 0.0, 0.0])

    def test_mirror(self):
        props, luxcore_name, prefix = export_first_mat("mirror")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["mirror"])
        assertListsAlmostEqual(self, props.Get(prefix + ".kr").Get(), [0.5, 0.0, 0.0])

    def test_glossy2(self):
        props, luxcore_name, prefix = export_first_mat("glossy2")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["glossy2"])
        assertListsAlmostEqual(self, props.Get(prefix + ".kd").Get(), [0.5, 0.0, 0.0])
        assertListsAlmostEqual(self, props.Get(prefix + ".ks").Get(), [0.1, 0.1, 0.1])
        assertListsAlmostEqual(self, props.Get(prefix + ".ka").Get(), [0.0, 0.0, 0.2])
        assertAlmostEqual(self, props.Get(prefix + ".uroughness").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".vroughness").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".d").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".multibounce").Get(), [False])


# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestMaterials)
unittest.TextTestRunner().run(suite)

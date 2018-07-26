import unittest
import sys

import BlendLuxCore
from BlendLuxCore.bin import pyluxcore
from BlendLuxCore import utils
from BlendLuxCore.nodes.output import get_active_output
from BlendLuxCore.export import Exporter
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

    luxcore_name = utils.get_luxcore_name(mat, is_viewport_render=False)
    props = pyluxcore.Properties()

    # Now export the material node tree, starting at the output node
    exporter = Exporter(bpy.context.scene)
    active_output.export(exporter, props, luxcore_name)
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

    def test_metal2(self):
        props, luxcore_name, prefix = export_first_mat("metal2")

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

    def test_glossytranslucent(self):
        props, luxcore_name, prefix = export_first_mat("glossytranslucent")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["glossytranslucent"])
        assertListsAlmostEqual(self, props.Get(prefix + ".kd").Get(), [0.5, 0.0, 0.0])
        assertListsAlmostEqual(self, props.Get(prefix + ".kt").Get(), [0.5, 0.0, 0.0])

        # Front face
        assertListsAlmostEqual(self, props.Get(prefix + ".ks").Get(), [0.1, 0.1, 0.1])
        assertListsAlmostEqual(self, props.Get(prefix + ".ka").Get(), [0.0, 0.0, 0.2])
        assertAlmostEqual(self, props.Get(prefix + ".uroughness").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".vroughness").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".d").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".multibounce").Get(), [False])

        # Back face
        assertListsAlmostEqual(self, props.Get(prefix + ".ks_bf").Get(), [0.1, 0.1, 0.1])
        assertListsAlmostEqual(self, props.Get(prefix + ".ka_bf").Get(), [0.0, 0.0, 0.2])
        assertAlmostEqual(self, props.Get(prefix + ".uroughness_bf").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".vroughness_bf").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".d_bf").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".multibounce_bf").Get(), [False])

    def test_glossycoating(self):
        props, luxcore_name, prefix = export_first_mat("glossycoating")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["glossycoating"])
        assertListsAlmostEqual(self, props.Get(prefix + ".ks").Get(), [0.1, 0.1, 0.1])
        assertListsAlmostEqual(self, props.Get(prefix + ".ka").Get(), [0.0, 0.0, 0.2])
        assertAlmostEqual(self, props.Get(prefix + ".uroughness").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".vroughness").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".d").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".multibounce").Get(), [False])
        # TODO test if base material was exported correctly

    def test_glass(self):
        props, luxcore_name, prefix = export_first_mat("glass")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["glass"])
        assertListsAlmostEqual(self, props.Get(prefix + ".kt").Get(), [0.5, 0.0, 0.0])
        assertListsAlmostEqual(self, props.Get(prefix + ".kr").Get(), [0.5, 0.0, 0.0])
        assertAlmostEqual(self, props.Get(prefix + ".interiorior").Get(), [1.3])
        assertAlmostEqual(self, props.Get(prefix + ".cauchyc").Get(), [0.01])

    def test_roughglass(self):
        props, luxcore_name, prefix = export_first_mat("roughglass")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["roughglass"])
        assertListsAlmostEqual(self, props.Get(prefix + ".kt").Get(), [0.5, 0.0, 0.0])
        assertListsAlmostEqual(self, props.Get(prefix + ".kr").Get(), [0.5, 0.0, 0.0])
        assertAlmostEqual(self, props.Get(prefix + ".interiorior").Get(), [1.3])
        assertAlmostEqual(self, props.Get(prefix + ".uroughness").Get(), [0.1])
        assertAlmostEqual(self, props.Get(prefix + ".vroughness").Get(), [0.1])

    def test_archglass(self):
        props, luxcore_name, prefix = export_first_mat("archglass")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["archglass"])
        assertListsAlmostEqual(self, props.Get(prefix + ".kt").Get(), [0.5, 0.0, 0.0])
        assertListsAlmostEqual(self, props.Get(prefix + ".kr").Get(), [0.5, 0.0, 0.0])
        assertAlmostEqual(self, props.Get(prefix + ".interiorior").Get(), [1.3])

    def test_null(self):
        props, luxcore_name, prefix = export_first_mat("null")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["null"])
        assertListsAlmostEqual(self, props.Get(prefix + ".transparency").Get(), [0.5, 0.0, 0.0])

    def test_carpaint(self):
        props, luxcore_name, prefix = export_first_mat("carpaint")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["carpaint"])
        self.assertEqual(props.Get(prefix + ".preset").Get(), ["blue matte"])
        assertAlmostEqual(self, props.Get(prefix + ".d").Get(), [0.1])
        assertListsAlmostEqual(self, props.Get(prefix + ".ka").Get(), [0.0, 0.0, 0.2])
        # TODO the rest of the properties (in "manual" preset mode)

    def test_cloth(self):
        props, luxcore_name, prefix = export_first_mat("cloth")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["cloth"])
        # TODO the rest of the properties

    def test_velvet(self):
        props, luxcore_name, prefix = export_first_mat("velvet")

        self.assertEqual(props.Get(prefix + ".type").Get(), ["velvet"])
        # TODO the rest of the properties


# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestMaterials)
result = unittest.TextTestRunner().run(suite)

pyluxcore.SetLogHandler(None)
sys.exit(not result.wasSuccessful())

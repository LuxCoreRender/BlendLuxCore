import unittest

import BlendLuxCore
from BlendLuxCore.export import light
from BlendLuxCore.bin import pyluxcore
from BlendLuxCore import utils
import bpy


class TestPointLight(unittest.TestCase):
    def test_prop_export(self):
        # Test the property export
        obj = bpy.data.objects["Point"]
        luxcore_scene = pyluxcore.Scene()
        context = bpy.context
        props, exported_light = light.convert_lamp(obj, context.scene, context, luxcore_scene)

        # Check if export succeeded
        self.assertIsNotNone(exported_light)

        # Check properties for correctness
        all_exported_light_prefixes = props.GetAllUniqueSubNames('scene.lights')
        prefix = all_exported_light_prefixes[0]

        self.assertEqual(props.Get(prefix + ".type").Get(), ["point"])
        transformation = utils.matrix_to_list(obj.matrix_world, bpy.context.scene, apply_worldscale=True)
        self.assertEqual(props.Get(prefix + ".transformation").Get(), transformation)
        self.assertEqual(props.Get(prefix + ".importance").Get(), [2])
        self.assertEqual(props.Get(prefix + ".samples").Get(), [3])
        self.assertEqual(props.Get(prefix + ".power").Get(), [3])
        self.assertEqual(props.Get(prefix + ".efficency").Get(), [12])

        gain = props.Get(prefix + ".gain").Get()
        expected_gain = [0.7 * 4, 0.6 * 4, 0.5 * 4]
        self.assertEqual(len(gain), len(expected_gain))
        for i in range(len(gain)):
            self.assertAlmostEqual(gain[i], expected_gain[i], places=3)

    def test_not_a_lamp(self):
        obj = bpy.data.objects["Plane"]
        luxcore_scene = pyluxcore.Scene()
        context = bpy.context
        print("=== Note: this test prints a stacktrace even if it succeeds ===")
        props, exported_light = light.convert_lamp(obj, context.scene, context, luxcore_scene)
        # Export should fail
        self.assertIsNone(exported_light)


# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestPointLight)
unittest.TextTestRunner().run(suite)

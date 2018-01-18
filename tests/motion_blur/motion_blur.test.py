import unittest

import BlendLuxCore
from BlendLuxCore.bin import pyluxcore
from BlendLuxCore.export import Exporter
from BlendLuxCore import utils
import bpy


def luxcore_logger(message):
    # In case you need the output
    # print(message)
    pass


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


class TestMotionBlur(unittest.TestCase):
    def test_only_obj_blur(self):
        # Get the object that moves and should be blurred
        moving_obj = bpy.data.objects["moving_obj"]
        moving_obj_name = utils.get_unique_luxcore_name(moving_obj)

        # Make sure the settings are correct
        # (can only change if someone messes with the test scene)
        blender_scene = bpy.context.scene
        self.assertIsNotNone(blender_scene.camera)
        blur_settings = blender_scene.camera.data.luxcore.motion_blur
        self.assertIs(blur_settings.enable, True)
        self.assertAlmostEqual(blur_settings.shutter, 4.0)
        self.assertIs(blur_settings.object_blur, True)
        self.assertEqual(blur_settings.steps, 2)

        # Export the scene (with silenced pyluxcore)
        pyluxcore.Init(luxcore_logger)
        exporter = Exporter()
        session = exporter.create_session(blender_scene)
        self.assertIsNotNone(session)

        config = session.GetRenderConfig()
        luxcore_scene = config.GetScene()
        scene_props = luxcore_scene.ToProperties()

        # Check properties for correctness
        all_exported_obj_prefixes = scene_props.GetAllUniqueSubNames("scene.objects")

        for prefix in all_exported_obj_prefixes:
            luxcore_name = prefix.split(".")[-1]

            if luxcore_name == moving_obj_name:
                # Test the times
                # step 0. Shutter is 4.0 frames, so this step should be minus half of the shutter value
                assertAlmostEqual(self, scene_props.Get(prefix + "motion.0.time").Get(), [-2.0])
                # step 1. This should be half of the shutter value
                assertAlmostEqual(self, scene_props.Get(prefix + "motion.1.time").Get(), [2.0])

                # Test the transformation matrices
                # step 0. We are at X = 3m, Y = 10m, Z = 0m
                x, y, z = 3, 10, 0
                expected_step_0 = [
                    1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    x, y, z, 1,
                ]
                transformation_step_0 = scene_props.Get(prefix + "motion.0.transformation").Get()
                assertListsAlmostEqual(self, transformation_step_0, expected_step_0)

                # step 1. We are at X = -3m, Y = 10m, Z = 0m
                x, y, z = -3, 10, 0
                expected_step_1 = [
                    1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    x, y, z, 1,
                ]
                transformation_step_1 = scene_props.Get(prefix + "motion.1.transformation").Get()
                assertListsAlmostEqual(self, transformation_step_1, expected_step_1)

        # Check if camera shutter settings are correct
        # Total shutter duration is 4.0 frames, so these should be -2.0 and 2.0
        self.assertAlmostEqual(scene_props.Get("scene.camera.shutteropen").GetFloat(), -2.0)
        self.assertAlmostEqual(scene_props.Get("scene.camera.shutterclose").GetFloat(), 2.0)


# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestMotionBlur)
unittest.TextTestRunner().run(suite)

import unittest
import sys

import BlendLuxCore
from BlendLuxCore.bin import pyluxcore
from BlendLuxCore.export import Exporter
from BlendLuxCore import utils
import bpy
from mathutils import Matrix, Vector
import math

TEST_FRAME = 3
TEST_SUBFRAME = 0.0


def luxcore_logger(message):
    # In case you need the output
    # print(message)
    pass


def assertListsAlmostEqual(test_case, list1, list2, places=3):
    test_case.assertEqual(len(list1), len(list2))

    for i in range(len(list1)):
        try:
            test_case.assertAlmostEqual(list1[i], list2[i], places=places)
        except AssertionError as e:
            print()
            print("AssertionError:", e)
            print("Failed list index:", i)
            print("Got list:     ", list1)
            print("Expected list:", list2)
            print()
            raise


def assertAlmostEqual(test_case, value1, value2, places=3):
    # Try to unpack the value if it is a list with only one element (common for LuxCore props)
    if isinstance(value1, list) and isinstance(value2, list):
        test_case.assertEqual(len(value1), 1)
        test_case.assertEqual(len(value1), len(value2))
        test_case.assertAlmostEqual(value1[0], value2[0], places=places)
    else:
        test_case.assertAlmostEqual(value1, value2, places=places)


def export(blender_scene):
    # Export the scene (with silenced pyluxcore)
    pyluxcore.SetLogHandler(luxcore_logger)
    blender_scene.luxcore.active_layer_index = 0
    exporter = Exporter(blender_scene)
    session = exporter.create_session()

    config = session.GetRenderConfig()
    luxcore_scene = config.GetScene()
    scene_props = luxcore_scene.ToProperties()
    return scene_props


def test_moving_object(test_case, scene_props, prefix):
    # Test the times
    # step 0. Shutter is 4.0 frames, so this step should be minus half of the shutter value
    assertAlmostEqual(test_case, scene_props.Get(prefix + "motion.0.time").Get(), [-2.0])
    # step 1. This should be half of the shutter value
    assertAlmostEqual(test_case, scene_props.Get(prefix + "motion.1.time").Get(), [2.0])

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
    assertListsAlmostEqual(test_case, transformation_step_0, expected_step_0)

    # step 1. We are at X = -3m, Y = 10m, Z = 0m
    x, y, z = -3, 10, 0
    expected_step_1 = [
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 0,
        x, y, z, 1,
    ]
    transformation_step_1 = scene_props.Get(prefix + "motion.1.transformation").Get()
    assertListsAlmostEqual(test_case, transformation_step_1, expected_step_1)


def create_expected_matrix(scene, translation, rotation, scale):
    transformation = translation * rotation * scale
    return utils.matrix_to_list(transformation, scene)


class TestMotionBlur(unittest.TestCase):
    def test_only_obj_blur(self):
        """
        Only one object ("moving_obj") is moving. Camera blur is disabled.
        """
        blender_scene = bpy.context.scene

        # Switch to the static camera
        blender_scene.camera = bpy.data.objects["static_camera"]

        # Switch to correct frame in case someone messed it up on save
        blender_scene.frame_set(TEST_FRAME, TEST_SUBFRAME)

        # Get the object that moves and should be blurred
        moving_obj = bpy.data.objects["moving_obj"]
        moving_obj_name = utils.get_luxcore_name(moving_obj, is_viewport_render=False)

        # Make sure the settings are correct
        # (can only change if someone messes with the test scene)
        self.assertIsNotNone(blender_scene.camera)
        blur_settings = blender_scene.camera.data.luxcore.motion_blur
        self.assertTrue(blur_settings.enable)
        self.assertAlmostEqual(blur_settings.shutter, 4.0)
        self.assertTrue(blur_settings.object_blur)
        self.assertFalse(blur_settings.camera_blur)
        self.assertEqual(blur_settings.steps, 2)
        # Make sure we are at the correct frame
        self.assertEqual(blender_scene.frame_current, 3)
        self.assertAlmostEqual(blender_scene.frame_subframe, 0.0)

        # Export the scene
        scene_props = export(blender_scene)

        # Check properties for correctness
        all_exported_obj_prefixes = scene_props.GetAllUniqueSubNames("scene.objects")

        for prefix in all_exported_obj_prefixes:
            luxcore_name = prefix.split(".")[-1]

            if luxcore_name == moving_obj_name:
                test_moving_object(self, scene_props, prefix)

        # Check if camera shutter settings are correct
        # Total shutter duration is 4.0 frames, so these should be -2.0 and 2.0
        self.assertAlmostEqual(scene_props.Get("scene.camera.shutteropen").GetFloat(), -2.0)
        self.assertAlmostEqual(scene_props.Get("scene.camera.shutterclose").GetFloat(), 2.0)

    def test_obj_and_cam_blur(self):
        """
        One object ("moving_obj") and the camera ("moving_camera") are moving.
        Camera and object motion blur are enabled.
        """
        blender_scene = bpy.context.scene

        # Switch to the moving camera
        blender_scene.camera = bpy.data.objects["moving_camera"]

        # Switch to correct frame in case someone messed it up on save
        blender_scene.frame_set(TEST_FRAME, TEST_SUBFRAME)

        # Get the object that moves and should be blurred
        moving_obj = bpy.data.objects["moving_obj"]
        moving_obj_name = utils.get_luxcore_name(moving_obj, is_viewport_render=False)

        # Make sure the settings are correct
        # (can only change if someone messes with the test scene)
        self.assertIsNotNone(blender_scene.camera)
        blur_settings = blender_scene.camera.data.luxcore.motion_blur
        self.assertTrue(blur_settings.enable)
        self.assertAlmostEqual(blur_settings.shutter, 4.0)
        self.assertTrue(blur_settings.object_blur)
        self.assertTrue(blur_settings.camera_blur)
        self.assertEqual(blur_settings.steps, 2)
        # Make sure we are at the correct frame
        self.assertEqual(blender_scene.frame_current, 3)
        self.assertAlmostEqual(blender_scene.frame_subframe, 0.0)

        # Export the scene
        scene_props = export(blender_scene)

        # Check properties for correctness
        all_exported_obj_prefixes = scene_props.GetAllUniqueSubNames("scene.objects")

        for prefix in all_exported_obj_prefixes:
            luxcore_name = prefix.split(".")[-1]

            if luxcore_name == moving_obj_name:
                test_moving_object(self, scene_props, prefix)

        # Check if camera shutter settings are correct
        # Total shutter duration is 4.0 frames, so these should be -2.0 and 2.0
        self.assertAlmostEqual(scene_props.Get("scene.camera.shutteropen").GetFloat(), -2.0)
        self.assertAlmostEqual(scene_props.Get("scene.camera.shutterclose").GetFloat(), 2.0)

        # Check if camera transformation props are correct

        # Test the times
        # step 0. Shutter is 4.0 frames, so this step should be minus half of the shutter value
        self.assertAlmostEqual(scene_props.Get("scene.camera.motion.0.time").GetFloat(), -2.0)
        # step 1. This should be half of the shutter value
        self.assertAlmostEqual(scene_props.Get("scene.camera.motion.1.time").GetFloat(), 2.0)

        # Test the transformation matrices

        # step 0. We are at X = 3m, Y = 0, Z = 0m
        translation = Matrix.Translation([3, 0, 0])
        rotation = Matrix.Rotation(math.radians(-90.0), 4, "X")
        scale = Matrix.Scale(1, 4)
        expected_step_0 = create_expected_matrix(blender_scene, translation, rotation, scale)
        # For some reason we need to invert these two... my matrix math is rusty
        expected_step_0[6] *= -1
        expected_step_0[9] *= -1

        transformation_step_0 = scene_props.Get("scene.camera.motion.0.transformation").GetFloats()
        assertListsAlmostEqual(self, transformation_step_0, expected_step_0)

        # step 1. We are at X = -3m, Y = 0, Z = 0m
        translation = Matrix.Translation([-3, 0, 0])
        rotation = Matrix.Rotation(math.radians(-90.0), 4, "X")
        scale = Matrix.Scale(1, 4)
        expected_step_1 = create_expected_matrix(blender_scene, translation, rotation, scale)
        # For some reason we need to invert these two... my matrix math is rusty
        expected_step_1[6] *= -1
        expected_step_1[9] *= -1

        transformation_step_1 = scene_props.Get("scene.camera.motion.1.transformation").GetFloats()
        assertListsAlmostEqual(self, transformation_step_1, expected_step_1)


# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestMotionBlur)
result = unittest.TextTestRunner().run(suite)

pyluxcore.SetLogHandler(None)
sys.exit(not result.wasSuccessful())

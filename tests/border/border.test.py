import unittest
import sys

import BlendLuxCore
from BlendLuxCore.export import Exporter, config
from BlendLuxCore.bin import pyluxcore
from BlendLuxCore import utils
import bpy


# Note: The expected resolutions in this file stem 
# from Blender Internal and Cycles test renders.


def check_resolution(testclass, props, expected_x, expected_y):
    # Get() returns a list with one value, unpack it
    x = props.Get("film.width").Get()[0]
    y = props.Get("film.height").Get()[0]
    testclass.assertEqual(x, expected_x)
    testclass.assertEqual(y, expected_y)


class TestBorder(unittest.TestCase):
    def test_final_uncropped(self):
        scene = bpy.context.scene
        # Blender expects a cropped image in all cases
        scene.render.use_crop_to_border = False

        scene.luxcore.active_layer_index = 0
        exporter = Exporter(scene)
        
        props = config.convert(exporter, scene)
        check_resolution(self, props, 30, 10)
        
    def test_final_cropped(self):
        scene = bpy.context.scene
        scene.render.use_crop_to_border = True

        scene.luxcore.active_layer_index = 0
        exporter = Exporter(scene)

        props = config.convert(exporter, scene)
        check_resolution(self, props, 30, 10)

    def test_different_resolution(self):
        scene = bpy.context.scene

        backup_x = scene.render.resolution_x
        backup_y = scene.render.resolution_y

        scene.render.resolution_x = 543
        scene.render.resolution_y = 789
        scene.render.use_crop_to_border = False

        scene.luxcore.active_layer_index = 0
        exporter = Exporter(scene)
        props = config.convert(exporter, scene)

        # Restore original resolution
        scene.render.resolution_x = backup_x
        scene.render.resolution_y = backup_y

        check_resolution(self, props, 163, 79)

# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestBorder)
result = unittest.TextTestRunner().run(suite)

pyluxcore.SetLogHandler(None)
sys.exit(not result.wasSuccessful())

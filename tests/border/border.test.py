import unittest

import BlendLuxCore
from BlendLuxCore.export import config
from BlendLuxCore.bin import pyluxcore
from BlendLuxCore import utils
import bpy


# Note: The expected resolutions in this file stem 
# from Blender Internal and Cycles test renders.


def check_resolution(testclass, props, expected_x, expected_y):
    testclass.assertEqual(props.Get("film.width").Get(), [expected_x])
    testclass.assertEqual(props.Get("film.height").Get(), [expected_y])


class TestBorder(unittest.TestCase):
    def test_final_uncropped(self):
        # Blender expects a cropped image in all cases
        bpy.context.scene.render.use_crop_to_border = False
        props = config.convert(bpy.context.scene)
        check_resolution(self, props, 30, 10)
        
    def test_final_cropped(self):
        bpy.context.scene.render.use_crop_to_border = True
        props = config.convert(bpy.context.scene)
        check_resolution(self, props, 30, 10)


# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestBorder)
unittest.TextTestRunner().run(suite)

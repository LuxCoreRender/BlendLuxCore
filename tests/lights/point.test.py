import unittest

import BlendLuxCore
from BlendLuxCore.export import light
import bpy


class TestPointLight(unittest.TestCase):
    def test_prop_export(self):
        # Test the property export
        obj = bpy.data.objects["Point"]
        props = light.convert(obj, bpy.context.scene)
        # TODO: test for correctness (but implement object/light
        # TODO: deletion first as it will probably change the signature)



# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestPointLight)
unittest.TextTestRunner().run(suite)

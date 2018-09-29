import unittest
import sys

# import the already loaded addon
import BlendLuxCore
from BlendLuxCore.bin import pyluxcore


class TestAddon(unittest.TestCase):
    def test_addon_enabled(self):
        # test if addon got loaded correctly
        # every addon must provide the "bl_info" dict
        self.assertIsNotNone(BlendLuxCore.bl_info)

# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestAddon)
result = unittest.TextTestRunner().run(suite)

pyluxcore.SetLogHandler(None)
sys.exit(not result.wasSuccessful())

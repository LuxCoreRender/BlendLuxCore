import unittest
from time import time
from contextlib import redirect_stdout

import BlendLuxCore
from BlendLuxCore import export
from BlendLuxCore.bin import pyluxcore
import bpy

# I silence this test because it creates a lot of log messages
# stdout of the addon is redirected to log.txt
# since this does not work for subprocesses like luxcore,
# I install an empty log handler there

def luxcore_logger(message):
    # In case you need the output
    # print(message)
    pass


class RenderEngineMockup:
    """ Simulates a bpy.types.RenderEngine class """    
    def __init__(self, abort_immediately=False):
        self.abort_immediately = abort_immediately

    def update_stats(self, arg1, arg2):
        pass

    def update_progress(self, value):
        pass

    def test_break(self):
        return self.abort_immediately


class TestFullExport(unittest.TestCase):
    def test_final_export(self):
        start = time()

        with open("./full_export/log.txt", "w") as log:
            with redirect_stdout(log):
                pyluxcore.Init(luxcore_logger)
                # Test final render export from the engine's point of view
                _exporter = export.Exporter()
                engine = RenderEngineMockup()
                _session = _exporter.create_session(bpy.context.scene, context=None, engine=engine)

        print("test_final_export(): Export took %.1fs" % (time() - start))

        # TODO: We could check a lot more here
        self.assertIsNotNone(_session)
    
    def test_user_abort(self):
        start = time()

        with open("./full_export/log.txt", "w") as log:
            with redirect_stdout(log):
                pyluxcore.Init(luxcore_logger)
                # Test user aborting the export process
                _exporter = export.Exporter()
                engine = RenderEngineMockup(abort_immediately=True)
                _session = _exporter.create_session(bpy.context.scene, context=None, engine=engine)

        print("test_user_abort(): Export took %.1fs" % (time() - start))

        self.assertIsNone(_session)


# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestFullExport)
unittest.TextTestRunner().run(suite)

import unittest
import sys

import BlendLuxCore
from BlendLuxCore.bin import pyluxcore
from BlendLuxCore.export import Exporter
from BlendLuxCore import utils
import bpy

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


class TestParticles(unittest.TestCase):
    def test_materials(self):
        blender_scene = bpy.context.scene

        # Export the scene
        scene_props = export(blender_scene)

        # Note: the "000" at the end of the name is there because LuxCore objects can only have
        # one material, while Blender objects can have multiple, so one Blender object might be
        # split into multiple LuxCore objects on export and an index is added to the name
        particle_base_obj = bpy.data.objects["ParticleBase"]
        particle_base_obj_name = utils.get_luxcore_name(particle_base_obj, is_viewport_render=False) + "000"
        particle_base_mat = particle_base_obj.material_slots[0].material
        particle_base_mat_name = utils.get_luxcore_name(particle_base_mat, is_viewport_render=False)

        emitter_obj = bpy.data.objects["Emitter"]
        emitter_obj_name = utils.get_luxcore_name(emitter_obj, is_viewport_render=False) + "000"
        emitter_mat = emitter_obj.material_slots[0].material
        emitter_mat_name = utils.get_luxcore_name(emitter_mat, is_viewport_render=False)

        # Check properties for correctness
        all_exported_obj_prefixes = scene_props.GetAllUniqueSubNames("scene.objects")

        for prefix in all_exported_obj_prefixes:
            luxcore_name = prefix.split(".")[-1]

            if luxcore_name == particle_base_obj_name:
                self.assertEqual(scene_props.Get(prefix + ".material").GetString(), particle_base_mat_name)
                mat_prefix = "scene.materials." + particle_base_mat_name
                # LuxCore inserts an implicit property texture here (probably because we use DuplicateObject)
                kd_tex_name = scene_props.Get(mat_prefix + ".kd").GetString()
                kd_tex_prefix = "scene.textures." + kd_tex_name
                assertListsAlmostEqual(self, scene_props.Get(kd_tex_prefix + ".value").GetFloats(), [0.7, 0.0, 0.0])
            elif luxcore_name == emitter_obj_name:
                self.assertEqual(scene_props.Get(prefix + ".material").GetString(), emitter_mat_name)
                mat_prefix = "scene.materials." + emitter_mat_name
                # LuxCore inserts an implicit property texture here (probably because we use DuplicateObject)
                kd_tex_name = scene_props.Get(mat_prefix + ".kd").GetString()
                kd_tex_prefix = "scene.textures." + kd_tex_name
                assertListsAlmostEqual(self, scene_props.Get(kd_tex_prefix + ".value").GetFloats(), [0.0, 0.7, 0.0])
            else:
                # It is one of the instanced particles
                self.assertEqual(scene_props.Get(prefix + ".material").GetString(), particle_base_mat_name)
                mat_prefix = "scene.materials." + particle_base_mat_name
                # LuxCore inserts an implicit property texture here (probably because we use DuplicateObject)
                kd_tex_name = scene_props.Get(mat_prefix + ".kd").GetString()
                kd_tex_prefix = "scene.textures." + kd_tex_name
                assertListsAlmostEqual(self, scene_props.Get(kd_tex_prefix + ".value").GetFloats(), [0.7, 0.0, 0.0])


# we have to manually invoke the test runner here, as we cannot use the CLI
suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestParticles)
result = unittest.TextTestRunner().run(suite)

pyluxcore.SetLogHandler(None)
sys.exit(not result.wasSuccessful())

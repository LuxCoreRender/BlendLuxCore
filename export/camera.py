import math
from mathutils import Vector
from ..bin import pyluxcore
from . import CacheEntry


def needs_update():
    # TODO (store info in cache or so? and rely on cam_obj.is_updated for stuff like special parameters?)
    return True


def convert(scene, context=None):
    print("converting camera")
    props = pyluxcore.Properties()

    if scene.camera:
        camera = scene.camera
        cameraDir = camera.matrix_world * Vector((0, 0, -1))
        props.Set(pyluxcore.Property("scene.camera.lookat.target", [cameraDir.x, cameraDir.y, cameraDir.z]))

        # Camera.location not always updated, but matrix is
        cameraLoc = camera.matrix_world.to_translation()
        props.Set(pyluxcore.Property("scene.camera.lookat.orig", [cameraLoc.x, cameraLoc.y, cameraLoc.z]))
        cameraUp = camera.matrix_world.to_3x3() * Vector((0, 1, 0))
        props.Set(pyluxcore.Property("scene.camera.up", [cameraUp.x, cameraUp.y, cameraUp.z]))

        fov = camera.data.angle * 180.0 / math.pi
        props.Set(pyluxcore.Property("scene.camera.fieldofview", fov))

    return props
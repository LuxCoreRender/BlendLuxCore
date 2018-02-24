from . import blender_object, camera, light, material, particle, scene, world


def init():
    blender_object.init()
    camera.init()
    light.init()
    material.init()
    particle.init()
    scene.init()
    world.init()

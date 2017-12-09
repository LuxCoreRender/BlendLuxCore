import bpy
from . import material, config


def init():
    material.init()
    config.init()
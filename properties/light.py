import bpy
from bpy.props import PointerProperty, EnumProperty, FloatProperty


def init():
    bpy.types.Lamp.luxcore = PointerProperty(type=LuxCoreLightProps)


class LuxCoreLightProps(bpy.types.PropertyGroup):
    # TODO have to find out if this is really the way to go
    # or if have to use the Blender type
    def update_type(self, context):
        lamp = context.lamp

        if self.type == "area":
            lamp.type = "AREA"
        elif self.type in ("sun", "distant"):
            lamp.type = "SUN"
        elif self.type in ("sky2", "infinite"):
            lamp.type = "HEMI"
        elif self.type == "point":
            lamp.type = "POINT"
        elif self.type in ("spot", "laser"):
            lamp.type = "SPOT"

    types = [
        ("area", "Area", "Mesh light", 0),
        ("sun", "Sun", "Simulates the sun, best used with a sky light", 1),
        ("sky2", "Sky", "Simulates the sky, can be used with a sun light", 2),
        # infinite and constantinfinite
        ("infinite", "HDRI", "Emitting light from all directions, used for environment lighting", 3),
        # point and mappoint
        ("point", "Point", "Emitting light from a point", 4),
        # spot and projector
        ("spot", "Spot", "Emitting light in a cone", 5),
        # distant and sharpdistant
        ("distant", "Distant", "Emitting parallel light rays from infinitely far away", 6),
        ("laser", "Laser", "Emitting parallel light rays", 7),
    ]
    type = EnumProperty(name="Type", items=types, update=update_type, default="area")

    gain = FloatProperty(name="Gain", description="Brightness multiplier", default=1, min=0)

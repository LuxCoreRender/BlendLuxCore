import bpy
from math import pi, cos, sin
from bgl import *
from .. import utils

handle = None


def handler():
    context = bpy.context

    if context.scene.render.engine != "LUXCORE":
        return

    obj = context.object

    if obj and obj.type == "LAMP" and obj.data.type == "POINT":
        lamp = obj.data
        radius = lamp.luxcore.radius

        if radius > 0:
            x, y, z = obj.matrix_world.to_translation()
            steps = 16
            # Optimization
            inv_steps = 1 / steps
            twice_pi = pi * 2

            theme = utils.get_theme(context)
            glColor3f(*theme.view_3d.object_active)

            glBegin(GL_LINE_LOOP)
            for i in range(steps):
                glVertex3f(
                    x + (radius * cos(i * twice_pi * inv_steps)),
                    y + (radius * sin(i * twice_pi * inv_steps)),
                    z
                )
            glEnd()

            glBegin(GL_LINE_LOOP)
            for i in range(steps):
                glVertex3f(
                    x,
                    y + (radius * cos(i * twice_pi * inv_steps)),
                    z + (radius * sin(i * twice_pi * inv_steps))
                )
            glEnd()

            glBegin(GL_LINE_LOOP)
            for i in range(steps):
                glVertex3f(
                    x + (radius * cos(i * twice_pi * inv_steps)),
                    y,
                    z + (radius * sin(i * twice_pi * inv_steps))
                )
            glEnd()

            # Reset color
            glColor4f(0.0, 0.0, 0.0, 1.0)

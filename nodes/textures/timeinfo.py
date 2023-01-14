import bpy
from ..base import LuxCoreNodeTexture
from ...handlers import frame_change_pre

class LuxCoreNodeTexTimeInfo(LuxCoreNodeTexture, bpy.types.Node):
    """ Access to time and frame information """
    bl_label = "Time Info"
    bl_width_default = 150

    def init(self, context):
        self.outputs.new("LuxCoreSocketFloatPositive", "Frame")
        self.outputs.new("LuxCoreSocketFloatPositive", "Time")

    def draw_buttons(self, context, layout):
        depsgraph = context.evaluated_depsgraph_get()
        scene = depsgraph.scene_eval

        milliseconds = scene.frame_current/scene.render.fps*1000
        seconds, milliseconds = divmod(milliseconds, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        col = layout.column(align=True)
        col.label(text='Frame: %s' % (scene.frame_current))
        col = layout.column(align=True)
        col.label(text='Time: %02d:%02d:%02d.%03d' % (hours, minutes, seconds, milliseconds))


    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        scene = depsgraph.scene_eval
        frame_change_pre.have_to_check_node_trees = True

        definitions = {
            "type": "constfloat1",
        }

        if output_socket == self.outputs["Time"]:
            definitions["value"] = scene.frame_current/scene.render.fps
        elif output_socket == self.outputs["Frame"]:
            definitions["value"] = scene.frame_current
        else:
            raise Exception("Unknown output socket:", output_socket)

        return self.create_props(props, definitions, luxcore_name)

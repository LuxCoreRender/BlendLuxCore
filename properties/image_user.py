from bpy.types import PropertyGroup
from bpy.props import IntProperty, BoolProperty


class LuxCoreImageUser(PropertyGroup):
    """
    We can't use Blender's ImageUser class, so we have to create our own.
    The ImageUser contains information about how an image is used by a datablock.
    For example, the same image sequence can be used with offset 5 by a pointlight
    and with offset 2 by an imagemap node, so the pointlight and the imagemap node
    each have their own ImageUser instance that saves this information.
    """

    frame_duration = IntProperty(name="Frames", min=1, default=1,
                                 description="Number of frames of a sequence to use")
    frame_start = IntProperty(name="Start Frame", default=1,
                              description="Global starting frame of the sequence, assuming first picture has a #1")
    frame_offset = IntProperty(name="Offset", default=0,
                               description="Offset the number of the frame to use in the animation")
    use_cyclic = BoolProperty(name="Cyclic", default=False,
                              description="Cycle the images in the sequence")

    def get_frame(self, scene):
        frame = scene.frame_current
        frame = frame - self.frame_start + 1

        if self.use_cyclic:
            frame %= self.frame_duration
            if frame < 0:
                frame += self.frame_duration
            if frame == 0:
                frame = self.frame_duration

        if frame < 1:
            frame = 1
        elif frame > self.frame_duration:
            frame = self.frame_duration

        frame += self.frame_offset
        return frame

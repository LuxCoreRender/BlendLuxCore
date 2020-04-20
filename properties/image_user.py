import random
import bpy
from bpy.types import PropertyGroup
from bpy.props import IntProperty, BoolProperty, PointerProperty, EnumProperty
from .. import utils
from ..ui import icons


FIRST_FRAME_DESC = (
    "Raise this value if you want to leave out frames from the beginning of the sequence"
)

LAST_FRAME_DESC = (
    "Lower this value if you want to leave out frames from the end of the sequence"
)

SEED_DESC = (
    "Seed of the random number. Change to get a different sequence of random numbers "
    "(e.g. if you have two image sequences and they should not pick the same frame, "
    "use a different seed on each imagemap node)"
)

WRAP_NONE_DESC = (
    "No wrapping is performed. If the image sequence does not contain enough "
    "frames to cover the whole animation, some frames will be missing. "
    "Only use this option if the sequence contains enough frames"
)


class LuxCoreImageUser(PropertyGroup):
    """
    We can't use Blender's ImageUser class, so we have to create our own.
    The ImageUser contains information about how an image is used by a datablock.
    For example, the same image sequence can be used with offset 5 by a pointlight
    and with offset 2 by an imagemap node, so the pointlight and the imagemap node
    each have their own ImageUser instance that saves this information.
    """

    # This image reference is just for internal bookkeeping
    image: PointerProperty(type=bpy.types.Image)

    first_frame: IntProperty(name="First Frame", default=1, min=1,  description=FIRST_FRAME_DESC)
    last_frame: IntProperty(name="Last Frame", default=2, min=1, description=LAST_FRAME_DESC)
    # TODO description?
    frame_offset: IntProperty(name="Offset", default=0)

    pick_random: BoolProperty(name="Pick Random", default=False,
                               description="Pick a random frame n so that: First Frame <= n <= Last Frame")
    seed: IntProperty(name="Seed", default=0, description=SEED_DESC)
    reverse: BoolProperty(name="Reverse", default=False,
                           description="Reverse the number of frames in the sequence")

    wrap_modes = [
        ("none", "None", WRAP_NONE_DESC, 0),
        ("clamp", "Clamp", "Use the first (or last) frame of the sequence: 111 12345 555", 1),
        ("repeat", "Repeat", "Loop the sequence: 12345 12345 12345", 2),
        ("pingpong", "Ping-Pong", "Like repeat, but every second repetition is reversed: 12345 54321 12345", 3),
    ]
    wrap_mode: EnumProperty(name="Wrap", items=wrap_modes, default="clamp",
                             description="How to handle the case of being outside of the sequence range")

    def update(self, image):
        """ This function should be called on each image update """
        if image and self.image != image:
            # A new or different image was linked,
            # auto-detect sequence length and first frame offset
            if image.source == "SEQUENCE":
                indexed_filepaths = utils.image_sequence_resolve_all(image)

                if indexed_filepaths:
                    first_index, first_path = indexed_filepaths[0]
                    frame_count = len(indexed_filepaths)
                    self.first_frame = 1
                    self.last_frame = frame_count
                    self.frame_offset = -first_index + 1
        self.image = image

    def get_frame(self, scene):
        """
        Calculate the current frame in the sequence.
        Note that the frame numbering starts at 1 and ends at frame_count (see below).
        """
        frame = scene.frame_current + self.frame_offset

        if self.first_frame > self.last_frame:
            raise ValueError("First frame greater than last frame")

        if self.pick_random:
            random.seed(self.seed ^ frame)
            return random.randint(self.first_frame, self.last_frame)

        frame_count = self.last_frame - self.first_frame + 1

        if self.wrap_mode == "clamp":
            frame = utils.clamp(frame, self.first_frame, self.last_frame)
        elif self.wrap_mode == "repeat":
            frame -= 1
            frame %= frame_count
            frame += 1
            frame += self.first_frame - 1
        elif self.wrap_mode == "pingpong":
            # Ping-Pong is like repeat, but every second repetition is reversed.
            # Note that this means that the first and last frame appear to be doubled.
            # E.g. with 5 frames:
            # Repeat:    12345 12345 12345
            # Ping-Pong: 12345 54321 12345
            frame %= frame_count * 2
            temp = frame
            frame = frame_count - abs(frame - frame_count)

            if temp > frame_count:
                frame += 1

            frame += self.first_frame - 1
            frame = utils.clamp(frame, self.first_frame, self.last_frame)

        if self.reverse:
            # We have to undo the first frame offset before reversing, then add it again
            frame -= self.first_frame - 1
            frame = frame_count - frame + 1
            frame += self.first_frame - 1

        return frame

    def draw(self, layout, scene):
        if self.image and self.image.source == "SEQUENCE":
            box = layout.box()
            sub = box.column(align=True)

            try:
                frame = self.get_frame(scene)
                sub.label(text="Frame: %d" % frame)
                if frame < self.first_frame or frame > self.last_frame:
                    sub.label(text="Out of range", icon=icons.WARNING)
            except ValueError as error:
                sub.label(text=str(error), icon=icons.ERROR)

            sub.prop(self, "first_frame")
            sub.prop(self, "last_frame")
            sub.prop(self, "frame_offset")

            sub.prop(self, "pick_random")
            if self.pick_random:
                sub.prop(self, "seed")

            sub2 = sub.column(align=True)
            sub2.active = not self.pick_random
            sub2.prop(self, "reverse")
            sub2.prop(self, "wrap_mode")

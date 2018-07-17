import bpy
from bpy.types import PropertyGroup


def get_active_stats():
    ...


class LuxCoreRenderStats:
    def __init__(self):
        self.export_time = 0


class LuxCoreRenderStatsCollection(PropertyGroup):
    slots = [LuxCoreRenderStats() for i in range(8)]

    def __getitem__(self, slot_index):
        return self.slots[slot_index]

    def reset(self, slot_index):
        self.slots[slot_index] = LuxCoreRenderStats()

    def get_active(self):
        render_result = None

        for image in bpy.data.images:
            if image.type == "RENDER_RESULT":
                render_result = image

        if not render_result:
            return None

        slot_index = render_result.render_slots.active_index
        return self.slots[slot_index]

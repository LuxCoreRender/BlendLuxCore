from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, FloatVectorProperty
from .. import LuxCoreNodeTexture


class ColorRampItem(PropertyGroup):
    offset = FloatProperty(name="Offset", default=0.0, min=0, max=1)
    value = FloatVectorProperty(name="", min=0, soft_max=1, subtype="COLOR")


class LuxCoreNodeTexBand(LuxCoreNodeTexture):
    bl_label = "Band"
    bl_width_min = 200

    interpolation_items = [
        ("linear", "Linear", "Linear interpolation between values, smooth transition", 0),
        ("cubic", "Cubic", "Cubic interpolation between values, smooth transition", 1),
        ("none", "None", "No interpolation between values, sharp transition", 2),
    ]
    interpolation = EnumProperty(name="Mode", description="Interpolation type of band values",
                                 items=interpolation_items, default="linear")

    def update_add(self, context):
        if len(self.items) == 1:
            new_offset = 1
            new_value = (1, 1, 1)
        else:
            max = None

            for item in self.items:
                if max is None or item.offset > max.offset:
                    max = item

            new_offset = max.offset
            new_value = max.value

        new_item = self.items.add()
        new_item.offset = new_offset
        new_item.value = new_value
        self["add_item"] = False

    def update_remove(self, context):
        if len(self.items) > 2:
            self.items.remove(len(self.items) - 1)
        self["remove_item"] = False
    
    def init(self, context):
        self.add_input("LuxCoreSocketFloat0to1", "Amount", 1)

        self.outputs.new("LuxCoreSocketColor", "Color")

        # Add inital items
        item_0 = self.items.add()
        item_0.offset = 0
        item_0.value = (0, 0, 0)

        item_1 = self.items.add()
        item_1.offset = 1
        item_1.value = (1, 1, 1)

    # This is a bit of a hack, we use BoolProperties as buttons
    add_item = BoolProperty(name="Add", description="Add an offset",
                            default=False, update=update_add)
    remove_item = BoolProperty(name="Remove", description="Remove last offset",
                               default=False, update=update_remove)
    items = CollectionProperty(type=ColorRampItem)

    def draw_buttons(self, context, layout):
        layout.prop(self, "interpolation", expand=True)

        row = layout.row(align=True)
        row.prop(self, "add_item", icon="ZOOMIN")

        subrow = row.row(align=True)
        subrow.enabled = len(self.items) > 2
        subrow.prop(self, "remove_item", icon="ZOOMOUT")

        for item in self.items:
            split = layout.split(align=True, percentage=0.7)
            split.prop(item, "offset", slider=True)
            split.prop(item, "value")

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "band",
            "interpolation": self.interpolation,
            "amount": self.inputs["Amount"].export(props),
        }
        
        for index, item in enumerate(self.items):            
            definitions["offset%d" % index] = item.offset
            definitions["value%d" % index] = list(item.value)

        return self.base_export(props, definitions, luxcore_name)

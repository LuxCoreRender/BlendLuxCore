from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, StringProperty
from .. import LuxCoreNodeTexture
from ...ui import icons


class ColorRampItem(PropertyGroup):
    offset = FloatProperty(name="Offset", default=0.0, min=0, max=1)
    value = FloatVectorProperty(name="", min=0, soft_max=1, subtype="COLOR")
    # For internal use
    index = IntProperty()
    node_name = StringProperty()

    def update_add_keyframe(self, context):
        data_path = 'nodes["%s"].ramp_items[%d]' % (self.node_name, self.index)
        self.id_data.keyframe_insert(data_path=data_path + ".offset")
        self.id_data.keyframe_insert(data_path=data_path + ".value")
        self["add_keyframe"] = False

    def update_remove_keyframe(self, context):
        data_path = 'nodes["%s"].ramp_items[%d]' % (self.node_name, self.index)
        self.id_data.keyframe_delete(data_path=data_path + ".offset")
        self.id_data.keyframe_delete(data_path=data_path + ".value")
        self["remove_keyframe"] = False

    # This is a bit of a hack, we use BoolProperties as buttons
    add_keyframe = BoolProperty(name="", description="Add a keyframe on the current frame",
                                default=False, update=update_add_keyframe)
    remove_keyframe = BoolProperty(name="", description="Remove the keyframe on the current frame",
                                   default=False, update=update_remove_keyframe)


class LuxCoreNodeTexBand(LuxCoreNodeTexture):
    bl_label = "Band"
    bl_width_default = 200

    interpolation_items = [
        ("linear", "Linear", "Linear interpolation between values, smooth transition", 0),
        ("cubic", "Cubic", "Cubic interpolation between values, smooth transition", 1),
        ("none", "None", "No interpolation between values, sharp transition", 2),
    ]
    interpolation = EnumProperty(name="Mode", description="Interpolation type of band values",
                                 items=interpolation_items, default="linear")

    def update_add(self, context):
        if len(self.ramp_items) == 1:
            new_offset = 1
            new_value = (1, 1, 1)
        else:
            max_item = None

            for item in self.ramp_items:
                if max_item is None or item.offset > max_item.offset:
                    max_item = item

            new_offset = max_item.offset
            new_value = max_item.value

        new_item = self.ramp_items.add()
        new_item.offset = new_offset
        new_item.value = new_value
        new_item.index = len(self.ramp_items) - 1
        new_item.node_name = self.name

        self["add_item"] = False

    def update_remove(self, context):
        if len(self.ramp_items) > 2:
            self.ramp_items.remove(len(self.ramp_items) - 1)
        self["remove_item"] = False

    # This is a bit of a hack, we use BoolProperties as buttons
    add_item = BoolProperty(name="Add", description="Add an offset",
                            default=False, update=update_add)
    remove_item = BoolProperty(name="Remove", description="Remove last offset",
                               default=False, update=update_remove)
    ramp_items = CollectionProperty(type=ColorRampItem)
    
    def init(self, context):
        self.add_input("LuxCoreSocketFloat0to1", "Amount", 1)

        self.outputs.new("LuxCoreSocketColor", "Color")

        # Add inital items
        item_0 = self.ramp_items.add()
        item_0.offset = 0
        item_0.value = (0, 0, 0)
        item_0.index = 0
        item_0.node_name = self.name

        item_1 = self.ramp_items.add()
        item_1.offset = 1
        item_1.value = (1, 1, 1)
        item_1.index = 1
        item_1.node_name = self.name

    def copy(self, orig_node):
        for item in self.ramp_items:
            # We have to update the parent node's name by hand because it's a StringProperty
            item.node_name = self.name

    def draw_buttons(self, context, layout):
        layout.prop(self, "interpolation", expand=True)

        row = layout.row(align=True)
        row.prop(self, "add_item", icon=icons.ADD)

        subrow = row.row(align=True)
        subrow.enabled = len(self.ramp_items) > 2
        subrow.prop(self, "remove_item", icon=icons.REMOVE)

        for index, item in enumerate(self.ramp_items):
            row = layout.row(align=True)

            split = row.split(align=True, percentage=0.55)
            split.prop(item, "offset", slider=True)
            split.prop(item, "value")

            node_tree = self.id_data
            anim_data = node_tree.animation_data
            # Keyframes are attached to fcurves, which are attached to the parent node tree
            if anim_data and anim_data.action:
                data_path = 'nodes["%s"].ramp_items[%d].offset' % (self.name, index)
                fcurves = (fcurve for fcurve in anim_data.action.fcurves if fcurve.data_path == data_path)

                fcurve_on_current_frame = False

                for fcurve in fcurves:
                    for keyframe_point in fcurve.keyframe_points:
                        frame = keyframe_point.co[0]
                        if frame == context.scene.frame_current:
                            fcurve_on_current_frame = True
                            break
            else:
                fcurve_on_current_frame = False

            if fcurve_on_current_frame:
                sub = row.row(align=True)
                # Highlight in red to show that a keyframe exists
                sub.alert = True
                sub.prop(item, "remove_keyframe", toggle=True, icon=icons.REMOVE_KEYFRAME)
            else:
                row.prop(item, "add_keyframe", toggle=True, icon=icons.ADD_KEYFRAME)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "band",
            "interpolation": self.interpolation,
            "amount": self.inputs["Amount"].export(exporter, props),
        }
        
        for index, item in enumerate(self.ramp_items):            
            definitions["offset%d" % index] = item.offset
            definitions["value%d" % index] = list(item.value)

        return self.create_props(props, definitions, luxcore_name)

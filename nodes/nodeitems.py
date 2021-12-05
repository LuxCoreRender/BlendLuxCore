from nodeitems_utils import NodeItemCustom


class Separator(NodeItemCustom):
    # NodeItemCustom is not documented anywhere so this code is a bit of guesswork
    def draw_separator(self, self2, layout, context):
        col = layout.column()
        col.scale_y = 0.2
        col.separator()

    def __init__(self, poll=None, draw=None):
        if draw is None:
            draw = self.draw_separator
        super().__init__(poll=poll, draw=draw)


class NodeItemMultiImageImport(NodeItemCustom):
    # NodeItemCustom is not documented anywhere so this code is a bit of guesswork
    def draw_operator(self, self2, layout, context):
        layout.operator("luxcore.import_multiple_images")

    def __init__(self, poll=None, draw=None):
        if draw is None:
            draw = self.draw_operator
        super().__init__(poll=poll, draw=draw)

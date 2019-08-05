
class State:
    active_view_layer = ""

    @classmethod
    def reset(cls):
        cls.active_view_layer = ""

def get_current_view_layer(scene):
    """ This is the layer that is currently being exported, not the active layer in the UI """
    # If active layer index is the empty string we are trying to access it
    # in an incorrect situation, e.g. viewport render
    if State.active_view_layer == "":
        return None

    return scene.view_layers[State.active_view_layer]
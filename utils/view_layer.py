
class State:
    active_view_layer_index = -1

    @classmethod
    def reset(cls):
        cls.active_view_layer_index = -1


def get_current_view_layer(scene):
    """ This is the layer that is currently being exported, not the active layer in the UI """
    # If active layer index is -1 we are trying to access it
    # in an incorrect situation, e.g. viewport render
    if State.active_view_layer_index == -1:
        return None

    return scene.view_layers[State.active_view_layer_index]
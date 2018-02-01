from . import get_name_with_lib


def template_node_tree(layout, data, property, icon,
                       menu,
                       operator_show="",
                       operator_new="",
                       operator_unlink=""):
    """
    Example usage:
    utils_ui.template_node_tree(layout, cam.luxcore, "volume", ICON_VOLUME,
                                "LUXCORE_VOLUME_MT_camera_select_volume_node_tree",
                                "luxcore.camera_show_volume_node_tree",
                                "luxcore.camera_new_volume_node_tree",
                                "luxcore.camera_unlink_volume_node_tree")
    """
    node_tree = getattr(data, property)

    split = layout.split(percentage=0.6, align=True)
    row = split.row(align=True)

    # Dropdown menu
    if node_tree:
        dropdown_text = get_name_with_lib(node_tree)
    else:
        dropdown_text = "---"

    row.menu(menu, icon=icon, text=dropdown_text)

    row = split.row(align=True)

    # Operator to quickly switch to this volume node tree
    if node_tree and operator_show:
        row.operator(operator_show)

    # Operator for new node tree
    if operator_new:
        new_text = "" if node_tree else "New"
        row.operator(operator_new, text=new_text, icon="ZOOMIN")

    # Operator to unlink node tree
    if node_tree and operator_unlink:
        row.operator(operator_unlink, text="", icon="X")
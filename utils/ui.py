from . import get_name_with_lib
from . import pluralize
from ..ui import icons


def template_node_tree(layout, data, property, icon,
                       menu,
                       operator_show="",
                       operator_new="",
                       operator_unlink=""):
    """
    Example usage:
    utils_ui.template_node_tree(layout, cam.luxcore, "volume", icons.NTREE_VOLUME,
                                "LUXCORE_VOLUME_MT_camera_select_volume_node_tree",
                                "luxcore.camera_show_volume_node_tree",
                                "luxcore.camera_new_volume_node_tree",
                                "luxcore.camera_unlink_volume_node_tree")
    """
    node_tree = getattr(data, property)

    split = layout.split(factor=0.6, align=True)
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
        row.operator(operator_new, text=new_text, icon=icons.ADD)

    # Operator to unlink node tree
    if node_tree and operator_unlink:
        row.operator(operator_unlink, text="", icon=icons.CLEAR)


def get_all_spaces(context, area_type, space_type):
    """
    Get all spaces of a specific area and space type.
    Area types: https://docs.blender.org/api/2.79/bpy.types.Area.html?highlight=area#bpy.types.Area.type
    Space types: https://docs.blender.org/api/2.79/bpy.types.Space.html?highlight=space#bpy.types.Space.type
    """
    spaces = []
    for area in context.screen.areas:
        if area.type == area_type:
            for space in area.spaces:
                if space.type == space_type:
                    spaces.append(space)
    return spaces


def get_all_regions(context, area_type, region_type):
    """
    Get all regions of a specific area and region type.
    Area types: https://docs.blender.org/api/2.79/bpy.types.Area.html?highlight=area#bpy.types.Area.type
    Region types: https://docs.blender.org/api/2.79/bpy.types.Region.html?highlight=region#bpy.types.Region.type
    """
    regions = []
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == area_type:
                for region in area.regions:
                    if region.type == region_type:
                        regions.append(region)
    return regions


def tag_region_for_redraw(context, area_type, region_type):
    """
    Force a region to redraw itself.
    This is necessary if some non-UI related code changes stuff in the UI
    and the user is currently not hovering the mouse over the affected
    panel. Example: On export, some errors are added to the error log.

    Example arguments: area_type == "PROPERTIES", region_type == "WINDOW"
    tags the properties for redraw.
    region_type can be "HEADER" or "WINDOW" in most cases
    """
    for region in get_all_regions(context, area_type, region_type):
        region.tag_redraw()


def humanize_time(seconds, show_subseconds=False, subsecond_places=3):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    strings = []
    if hours:
        strings.append(pluralize("%d hour", hours))
    if minutes:
        strings.append(pluralize("%d minute", minutes))

    if show_subseconds and seconds > 0:
        strings.append("%s seconds" % str(round(seconds, subsecond_places)))
    elif seconds:
        strings.append(pluralize("%d second", seconds))

    if strings:
        return ", ".join(strings)
    else:
        return "0 seconds"

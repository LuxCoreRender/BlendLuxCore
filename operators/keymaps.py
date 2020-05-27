import bpy


addon_keymaps = []


def register():
    # Don't register keymaps if blender is executed in background mode with '-b'
    if bpy.app.background:
        return
    wm = bpy.context.window_manager
    keymap = wm.keyconfigs.addon.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
    
    from .node_editor import (
        LUXCORE_OT_node_editor_viewer, 
        LUXCORE_OT_mute_node, 
        LUXCORE_OT_node_editor_add_image,
    )
    keymap_item = keymap.keymap_items.new(LUXCORE_OT_node_editor_viewer.bl_idname, "LEFTMOUSE", "PRESS", ctrl=True, shift=True)
    addon_keymaps.append((keymap, keymap_item))
    keymap_item = keymap.keymap_items.new(LUXCORE_OT_mute_node.bl_idname, "M", "PRESS")
    addon_keymaps.append((keymap, keymap_item))
    keymap_item = keymap.keymap_items.new(LUXCORE_OT_node_editor_add_image.bl_idname, "T", "PRESS", ctrl=True)
    addon_keymaps.append((keymap, keymap_item))
    

def unregister():
    if bpy.app.background:
        return
    for keymap, keymap_item in addon_keymaps:
        keymap.keymap_items.remove(keymap_item)
    addon_keymaps.clear()

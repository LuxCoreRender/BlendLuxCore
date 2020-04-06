# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import PointerProperty, IntProperty, BoolProperty, EnumProperty, FloatVectorProperty


def switch_search_results(self, context):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui

    #TODO:
    #if ui_props.asset_type == 'MODEL':
    #    scene['search results'] = scene.get('LOL model search')
    #    scene['search results orig'] = scene.get('LOL model search orig')
    #elif ui_props.asset_type == 'SCENE':
    #    scene['search results'] = scene.get('LOL scene search')
    #    scene['search results orig'] = scene.get('LOL scene search orig')
    #elif ui_props.asset_type == 'MATERIAL':
    #    scene['search results'] = scene.get('LOL material search')
    #    scene['search results orig'] = scene.get('LOL material search orig')
    #elif ui_props.asset_type == 'TEXTURE':
    #    scene['search results'] = scene.get('LOL texture search')
    #    scene['search results orig'] = scene.get('LOL texture search orig')
    #elif ui_props.asset_type == 'BRUSH':
    #    scene['search results'] = scene.get('LOL brush search')
    #    scene['search results orig'] = scene.get('LOL brush search orig')
    #search.load_previews()



class LuxCoreOnlineLibraryUI(bpy.types.PropertyGroup):
    ui_scale = 1
    thumb_size_def = 96
    margin_def = 0

    thumb_size: IntProperty(name="Thumbnail Size", default=96, min=-1, max=256)
    assetbar_on: BoolProperty(name="Assetbar On", default=False)
    turn_off: BoolProperty(name="Turn Off", default=False)

    asset_items = [
        ('MODEL', 'Model', 'Browse models', 'OBJECT_DATAMODE', 0),
        # ('SCENE', 'SCENE', 'Browse scenes', 'SCENE_DATA', 1),
        ('MATERIAL', 'Material', 'Browse models', 'MATERIAL', 2),
        # ('TEXTURE', 'Texture', 'Browse textures', 'TEXTURE', 3),
        ('BRUSH', 'Brush', 'Browse brushes', 'BRUSH_DATA', 3)
    ]
    asset_type: EnumProperty(name="Active Asset Type", items=asset_items, description="Activate asset in UI",
                             default="MODEL", update=switch_search_results)

    mouse_x: IntProperty(name="Mouse X", default=0)
    mouse_y: IntProperty(name="Mouse Y", default=0)

    active_index: IntProperty(name="Active Index", default=-3)
    scrolloffset: IntProperty(name="Scroll Offset", default=0)
    drawoffset: IntProperty(name="Draw Offset", default=0)

    dragging: BoolProperty(name="Dragging", default=False)
    drag_init: BoolProperty(name="Drag Initialisation", default=False)
    drag_length: IntProperty(name="Drag length", default=0)
    draw_drag_image: BoolProperty(name="Draw Drag Image", default=False)
    draw_snapped_bounds: BoolProperty(name="Draw Snapped Bounds", default=False)

    snapped_location: FloatVectorProperty(name="Snapped Location", default=(0, 0, 0))
    snapped_bbox_min: FloatVectorProperty(name="Snapped Bbox Min", default=(0, 0, 0))
    snapped_bbox_max: FloatVectorProperty(name="Snapped Bbox Max", default=(0, 0, 0))
    snapped_normal: FloatVectorProperty(name="Snapped Normal", default=(0, 0, 0))

    snapped_rotation: FloatVectorProperty(name="Snapped Rotation", default=(0, 0, 0), subtype='QUATERNION')

    bar_height: IntProperty(name="Bar Height", default=thumb_size_def + 2 * margin_def, min=-1, max=2048)
    bar_x_offset: IntProperty(name="Bar X Offset", default=20, min=0, max=5000)
    bar_y_offset: IntProperty(name="Bar Y Offset", default=80, min=0, max=5000)

    bar_x: IntProperty(name="Bar X", default=100, min=0, max=5000)
    bar_y: IntProperty(name="Bar Y", default=100, min=50, max=5000)
    bar_end: IntProperty(name="Bar End", default=100, min=0, max=5000)
    bar_width: IntProperty(name="Bar Width", default=100, min=0, max=5000)

    wcount: IntProperty(name="Width Count", default=10, min=0, max=5000)
    hcount: IntProperty(name="Rows", default=5, min=0, max=5000)

    margin: IntProperty(name="Margin", default=margin_def, min=-1, max=256)
    highlight_margin: IntProperty(name="Highlight Margin", default=int(margin_def / 2), min=-10, max=256)
    has_hit: BoolProperty(name="has_hit", default=False)


class LuxCoreOnlineLibraryModel(bpy.types.PropertyGroup):
    free_only: BoolProperty(name="Free only", default=True)
    append_method_items = [
        ('LINK_COLLECTION', 'Link Collection', ''),
        ('APPEND_OBJECTS', 'Append Objects', ''),
    ]
    append_method: EnumProperty(name = "Import Method", items = append_method_items,
    description = "choose if the assets will be linked or appended", default = "LINK_COLLECTION"

)

class LuxCoreOnlineLibraryScene(bpy.types.PropertyGroup):
    ui: PointerProperty(type=LuxCoreOnlineLibraryUI)
    model: PointerProperty(type=LuxCoreOnlineLibraryModel)

    @classmethod
    def register(cls):
        bpy.types.Scene.luxcoreOL = PointerProperty( name="LuxCore Online Library Settings",
            description="LuxCore Online Library settings", type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.luxcoreOL


#class LuxCoreOnlineLibrarySceneBrush(bpy.types.PropertyGroup):

#class LuxCoreOnlineLibrarySceneMaterial(bpy.types.PropertyGroup):
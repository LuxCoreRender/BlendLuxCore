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
# ##### END GPL LICENSE BLOCK ####
#
#  This code is based on the Blenderkit Addon
#  Homepage: https://www.blenderkit.com/
#  Sourcecode: https://github.com/blender/blender-addons/tree/master/blenderkit
#
# #####

import bpy
from math import pi
from bpy.props import CollectionProperty, PointerProperty, IntProperty, BoolProperty, EnumProperty, \
    FloatProperty, FloatVectorProperty, StringProperty
from ...utils.lol import utils as utils

def switch_local_free(self, context):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui

    utils.init_categories(context)
    ui_props.scrolloffset = 0


def switch_search_results(self, context):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui
    upload_props = scene.luxcoreOL.upload

    if not ui_props.ToC_loaded:
        utils.download_table_of_contents(context)

    assets = utils.get_search_props(context)
    ui_props.scrolloffset = 0

    if ui_props.asset_type == 'MODEL':
        asset_props = scene.luxcoreOL.model
        if not scene.luxcoreOL.model.thumbnails_loaded:
            utils.load_previews(context, ui_props.asset_type)
            scene.luxcoreOL.model.thumbnails_loaded = True
    if ui_props.asset_type == 'SCENE':
        asset_props = scene.luxcoreOL.scene
        if not scene.luxcoreOL.scene.thumbnails_loaded:
            utils.load_previews(context, ui_props.asset_type)
            scene.luxcoreOL.scene.thumbnails_loaded = True
    if ui_props.asset_type == 'MATERIAL':
        asset_props = scene.luxcoreOL.material
        if not scene.luxcoreOL.material.thumbnails_loaded:
            utils.load_previews(context, ui_props.asset_type)
            scene.luxcoreOL.material.thumbnails_loaded = True

    utils.init_categories(context)

    scene.luxcoreOL.on_search = False
    self.category = ""
    scene.luxcoreOL.search_category = self.category

    upload_props.add_list.clear()


class LuxCoreOnlineLibraryAssetBar(bpy.types.PropertyGroup):
    ui_scale = 1
    thumb_size_def = 96
    margin_def = 0

    height: IntProperty(name="Assetbar Height", default=thumb_size_def + 2 * margin_def, min=-1, max=2048)
    width: IntProperty(name="Assetbar Width", default=100, min=0, max=5000)

    x_offset: IntProperty(name="Bar X Offset", default=20, min=0, max=5000)
    y_offset: IntProperty(name="Bar Y Offset", default=100, min=0, max=5000)
    drawoffset: IntProperty(name="Draw Offset", default=0)

    x: IntProperty(name="Bar X", default=100, min=0, max=5000)
    y: IntProperty(name="Bar Y", default=100, min=50, max=5000)
    start: IntProperty(name="Bar Start", default=100, min=0, max=5000)
    end: IntProperty(name="Bar End", default=100, min=0, max=5000)

    drag_init: BoolProperty(name="Drag assetbar initialisation", default=False)
    drag_x: IntProperty(name="Drag bar x offset", default=0)
    drag_y: IntProperty(name="Drag bar y offset", default=0)
    dragging: BoolProperty(name="Dragging asset", default=False)

    resize_x_left: BoolProperty(name="Resize assetbar in x direction", default=False)
    resize_x_right: BoolProperty(name="Resize assetbar in x direction", default=False)
    resize_y_top: BoolProperty(name="Resize assetbar in y direction", default=False)
    resize_y_down: BoolProperty(name="Resize assetbar in y direction", default=False)
    resize_xy: IntProperty(name="Resize bar offset", default=0)
    resize_wh: IntProperty(name="Resize bar offset", default=0)

    wcount: IntProperty(name="Width Count", default=10, min=0, max=5000)
    hcount: IntProperty(name="Rows", default=5, min=0, max=5000)

    margin: IntProperty(name="Margin", default=margin_def, min=-1, max=256)
    highlight_margin: IntProperty(name="Highlight Margin", default=int(margin_def / 2), min=-10, max=256)


class LuxCoreOnlineLibraryUI(bpy.types.PropertyGroup):
    ui_scale = 1
    thumb_size_def = 96
    margin_def = 0

    thumb_size: IntProperty(name="Thumbnail Size", default=thumb_size_def, min=-1, max=256)
    assetbar_on: BoolProperty(name="Assetbar On", default=False)
    turn_off: BoolProperty(name="Turn Off", default=False)

    asset_items = [
        ('MODEL', 'Model', 'Browse models', 'OBJECT_DATAMODE', 0),
        # ('SCENE', 'SCENE', 'Browse scenes', 'SCENE_DATA', 1),
        ('MATERIAL', 'Material', 'Browse materials', 'MATERIAL', 2),
        # ('TEXTURE', 'Texture', 'Browse textures', 'TEXTURE', 3),
        # ('BRUSH', 'Brush', 'Browse brushes', 'BRUSH_DATA', 3)
    ]
    asset_type: EnumProperty(name="Active Asset Type", items=asset_items, description="Activate asset in UI",
                             default="MODEL", update=switch_search_results)

    mouse_x: IntProperty(name="Mouse X", default=0)
    mouse_y: IntProperty(name="Mouse Y", default=0)

    active_index: IntProperty(name="Active Index", default=-3)
    scrolloffset: IntProperty(name="Scroll Offset", default=0)

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

    has_hit: BoolProperty(name="has_hit", default=False)
    ToC_loaded: BoolProperty(name="ToC loaded", default=False, options={'SKIP_SAVE'})
    local: BoolProperty(name="Local only", default=False, update=switch_local_free)
    free_only: BoolProperty(name="Free only", default=False, update=switch_local_free)

    assetbar: PointerProperty(type=LuxCoreOnlineLibraryAssetBar)


class LuxCoreOnlineLibraryModel(bpy.types.PropertyGroup):
    thumbnails_loaded: BoolProperty(name="thumbnails_loaded", default=False, options={'SKIP_SAVE'})
    free_only: BoolProperty(name="Free only", default=False, update=switch_local_free)
    switched_append_method: BoolProperty(name="Switched Append Method", default=False)
    append_method_items = [
        ('LINK_COLLECTION', 'Link Collection', ''),
        ('APPEND_OBJECTS', 'Append Objects', ''),
    ]
    append_method: EnumProperty(name="Import Method", items=append_method_items,
    description="choose if the assets will be linked or appended", default="APPEND_OBJECTS")

    randomize_rotation: BoolProperty(name='Randomize Rotation',
                                     description="randomize rotation at placement",
                                     default=False)
    randomize_rotation_amount: FloatProperty(name="Randomization Max Angle",
                                             description="maximum angle for random rotation",
                                             default=pi / 36,
                                             min=0,
                                             max=2 * pi,
                                             subtype='ANGLE')
    offset_rotation_amount: FloatProperty(name="Offset Rotation",
                                          description="offset rotation, hidden prop",
                                          default=0,
                                          min=0,
                                          max=360,
                                          subtype='ANGLE')
    offset_rotation_step: FloatProperty(name="Offset Rotation Step",
                                        description="offset rotation, hidden prop",
                                        default=pi / 2,
                                        min=0,
                                        max=180,
                                        subtype='ANGLE')


class LuxCoreOnlineLibraryMaterial(bpy.types.PropertyGroup):
    thumbnails_loaded: BoolProperty(name="thumbnails_loaded", default=False, options={'SKIP_SAVE'})


class LuxCoreOnlineLibraryScene(bpy.types.PropertyGroup):
    thumbnails_loaded: BoolProperty(name="thumbnails_loaded", default=False, options={'SKIP_SAVE'})


class LuxCoreOnlineLibraryAsset(bpy.types.PropertyGroup):
    name: StringProperty(name="Asset name", description="Assign a name to the asset", default="Default")
    category: StringProperty(name="Category", description="Assign a category to the asset", default="misc")
    url: StringProperty(name="Url", description="Assign a category to the asset", default="")
    bbox_min: FloatVectorProperty(name="Bounding Box Min", default=(0, 0, 0))
    bbox_max: FloatVectorProperty(name="Bounding Box Max", default=(1, 1, 1))
    hash: StringProperty(name="Hash", description="SHA256 hash number for the asset blendfile", default="")
    show_settings: BoolProperty(default=False)
    show_thumbnail: BoolProperty(name="", default=True, description="Show thumbnail")
    thumbnail: PointerProperty(name="Image", type=bpy.types.Image)


class LuxCoreOnlineLibraryUpload(bpy.types.PropertyGroup):
    name: StringProperty(name="Asset name", description="Assign a name to the asset", default="Default")
    category: StringProperty(name='Category', description="Assign a category to the asset", default="misc")
    autorender: BoolProperty(name="Autorender thumbnail", default=True)
    samples: IntProperty(name="Samples", default=50, min=1)
    show_thumbnail: BoolProperty(name="", default=True, description="Show thumbnail")
    thumbnail: PointerProperty(name="Image", type=bpy.types.Image)
    add_list: CollectionProperty(type=LuxCoreOnlineLibraryAsset)


class LuxCoreOnlineLibrary(bpy.types.PropertyGroup):
    ui: PointerProperty(type=LuxCoreOnlineLibraryUI)
    model: PointerProperty(type=LuxCoreOnlineLibraryModel)
    material: PointerProperty(type=LuxCoreOnlineLibraryMaterial)
    scene: PointerProperty(type=LuxCoreOnlineLibraryScene)
    on_search: BoolProperty(name="on_search", default=False)
    search_category: StringProperty(name="search_category", default="")
    upload: PointerProperty(type=LuxCoreOnlineLibraryUpload)

    @classmethod
    def register(cls):
        bpy.types.Scene.luxcoreOL = PointerProperty( name="LuxCore Online Library Settings",
            description="LuxCore Online Library settings", type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.luxcoreOL


#class LuxCoreOnlineLibrarySceneBrush(bpy.types.PropertyGroup):


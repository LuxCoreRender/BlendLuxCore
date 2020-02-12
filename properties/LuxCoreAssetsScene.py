import bpy
from bpy.props import PointerProperty, IntProperty, BoolProperty, EnumProperty

#class LuxCoreAssetsModel(bpy.types.PropertyGroup):

#class LuxCoreAssetsScene(bpy.types.PropertyGroup):

#class LuxCoreAssetsBrush(bpy.types.PropertyGroup):

#class LuxCoreAssetsBrush(bpy.types.PropertyGroup):

def switch_search_results(self, context):
    scene = context.scene
    ui_props = scene.luxcore_assets.ui

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



class LuxCoreAssetsUI(bpy.types.PropertyGroup):
    thumb_size: IntProperty(name="Thumbnail Size", default=96, min=-1, max=256)
    assetbar_on: BoolProperty(name="Assetbar On", default=False)

    asset_items = [
        ('MODEL', 'Model', 'Browse models', 'OBJECT_DATAMODE', 0),
        # ('SCENE', 'SCENE', 'Browse scenes', 'SCENE_DATA', 1),
        ('MATERIAL', 'Material', 'Browse models', 'MATERIAL', 2),
        # ('TEXTURE', 'Texture', 'Browse textures', 'TEXTURE', 3),
        ('BRUSH', 'Brush', 'Browse brushes', 'BRUSH_DATA', 3)
    ]
    asset_type: EnumProperty(name="Active Asset Type", items=asset_items, description="Activate asset in UI",
                             default="MATERIAL", update=switch_search_results)

class LuxCoreAssetsModel(bpy.types.PropertyGroup):
    free_only: BoolProperty(name="Free only", default=True)
    append_method_items = [
        ('LINK_COLLECTION', 'Link Collection', ''),
        ('APPEND_OBJECTS', 'Append Objects', ''),
    ]
    append_method: EnumProperty(name = "Import Method", items = append_method_items,
    description = "choose if the assets will be linked or appended", default = "LINK_COLLECTION"

)

class LuxCoreAssetsScene(bpy.types.PropertyGroup):
    ui: PointerProperty(type=LuxCoreAssetsUI)
    model: PointerProperty(type=LuxCoreAssetsModel)

    @classmethod
    def register(cls):
        bpy.types.Scene.luxcore_assets = PointerProperty(
            name="LuxCore Asset Library Settings",
            description="LuxCore Asset Library settings",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.luxcoreAssets


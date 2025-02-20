import bpy
import sys
from os import listdir
from os.path import isfile, join, basename, dirname, splitext
from mathutils import Vector, Matrix

from BlendLuxCore.utils.compatibility import run


def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)


def calc_bbox(context, objects):
    bbox_min = [10000, 10000, 10000]
    bbox_max = [-10000, -10000, -10000]

    deps = bpy.context.evaluated_depsgraph_get()
    bpy.ops.object.select_all(action='DESELECT')
    
    for obj in objects:
        obj = obj.evaluated_get(deps)
        
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

        for corner in bbox_corners:
            bbox_min[0] = min(bbox_min[0], corner[0])
            bbox_min[1] = min(bbox_min[1], corner[1])
            bbox_min[2] = min(bbox_min[2], corner[2])

            bbox_max[0] = max(bbox_max[0], corner[0])
            bbox_max[1] = max(bbox_max[1], corner[1])
            bbox_max[2] = max(bbox_max[2], corner[2])

    return (bbox_min, bbox_max)


def render_material_thumbnail(assetname, blendfile, thumbnail, samples):
    context = bpy.context

    with bpy.data.libraries.load(blendfile, link=True) as (mat_from, mat_to):
        mat_to.materials = mat_from.materials

    mat = mat_to.materials[0]

    context.view_layer.objects.active = bpy.data.objects['Luxball']
    bpy.data.objects['Luxball'].material_slots[0].material = mat
    context.view_layer.objects.active = bpy.data.objects['Luxball ring']
    bpy.data.objects['Luxball ring'].material_slots[0].material = mat
    run()

    context.scene.view_settings.gamma = 1
    context.scene.view_settings.exposure = 1
    context.scene.view_settings.look = 'Very High Contrast'
    context.scene.luxcore.halt.enable = True
    context.scene.luxcore.halt.use_samples = True
    context.scene.luxcore.halt.samples = int(samples)
    context.scene.render.image_settings.file_format = 'JPEG'
    context.scene.render.filepath = thumbnail

    bpy.ops.render.render(write_still=True)


def render_model_thumbnail(assetname, blendfile, thumbnail, samples):
    context = bpy.context
    scene = context.scene
    
    with bpy.data.libraries.load(blendfile, link=True) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects]
   
    # Add new collection, where the assets are placed into
    col = bpy.data.collections.new(assetname)
    # Add parent empty for asset collection
    main_object = bpy.data.objects.new(assetname, None)
    main_object.instance_type = 'COLLECTION'
    main_object.instance_collection = col
    # Objects have to be linked to show up in a scene
    for obj in data_to.objects:
        # Add objects to asset collection
        col.objects.link(obj)
    run()
    scene.collection.objects.link(main_object)

    bbox_min, bbox_max = calc_bbox(context, data_to.objects) 
    print(bbox_min)
    print(bbox_max)
    
    bbox_center = 0.5 * Vector((bbox_max[0] + bbox_min[0], bbox_max[1] + bbox_min[1], 0))
    
    scale_size = 2 * max(abs(bbox_max[0] - bbox_min[0]), abs(bbox_max[2] - bbox_min[2]))
    
    background = [
        bpy.data.objects['Camera'],
        bpy.data.objects['Stage'],
        bpy.data.objects['Left Area'],
        bpy.data.objects['Right Area'],
        bpy.data.objects['Room'],
        bpy.data.objects['Top Area'],
        bpy.data.objects['Backlight Area']]
        
    camera = bpy.data.objects['Camera']
        
    select(background)
    context.scene.tool_settings.transform_pivot_point = 'CURSOR'  
    bpy.ops.transform.resize(value=(scale_size, scale_size, scale_size), center_override=(0.6, 0, 0))

    bpy.ops.object.select_all(action='DESELECT')
    
    camera.location.z = 0.5 * abs(bbox_max[2] - bbox_min[2])
    
        
    main_object.empty_display_size = 0.5 * max(bbox_max[0] - bbox_min[0], bbox_max[1] - bbox_min[1],
                                               bbox_max[2] - bbox_min[2])

    main_object.location = (0.6, 0, 0)
    main_object.rotation_euler = (0, 0, 0)
    main_object.empty_display_size = 0.5*max(bbox_max[0] - bbox_min[0], bbox_max[1] - bbox_min[1], bbox_max[2] - bbox_min[2])

    col.instance_offset = bbox_center
            
    context.scene.view_settings.gamma = 1
    context.scene.view_settings.exposure = 1
    context.scene.view_settings.look = 'Very High Contrast'
    context.scene.luxcore.halt.enable = True
    context.scene.luxcore.halt.use_samples = True
    context.scene.luxcore.halt.samples = int(samples)
    context.scene.render.image_settings.file_format = 'JPEG'
    context.scene.render.filepath = thumbnail
    
    bpy.ops.render.render(write_still = True)



argv = sys.argv
argv = argv[argv.index("--") + 1:]

blendfile = argv[0]
assetname = splitext(basename(argv[0]))[0]
thumbnail = join(dirname(dirname(argv[0])), 'preview', 'full', 'local', assetname + ".jpg")
samples = argv[1]
type = argv[2]

if type == 'model':
    render_model_thumbnail(assetname, blendfile, thumbnail, samples)
elif type == 'material':
    render_material_thumbnail(assetname, blendfile, thumbnail, samples)
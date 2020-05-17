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
#
#  This code is based on the Blenderkit Addon
#  Homepage: https://www.blenderkit.com/
#  Sourcecode: https://github.com/blender/blender-addons/tree/master/blenderkit
#
# #####

import bpy


class OBJECT_MT_LOL_asset_menu(bpy.types.Menu):
    bl_label = "Asset options:"
    bl_idname = "OBJECT_MT_LOL_asset_menu"

    def draw(self, context):
        layout = self.layout
        ui_props = context.scene.luxcoreOL.ui

        assets = context.scene['assets']

        asset_data = assets[ui_props.active_index]
        #TODO: Implement
        #author_id = str(asset_data['author']['id'])

        wm = context.window_manager
        # if wm.get('bkit authors') is not None:
        #     a = context.window_manager['bkit authors'].get(author_id)
        #     if a is not None:
        #         # utils.p('author:', a)
        #         if a.get('aboutMeUrl') is not None:
        #             op = layout.operator('wm.url_open', text="Open Author's Website")
        #             op.url = a['aboutMeUrl']
        #
        #         op = layout.operator('view3d.blenderkit_search', text="Show Assets By Author")
        #         op.keywords = ''
        #         op.author_id = author_id

        # op = layout.operator('view3d.blenderkit_search', text='Search Similar')
        # op.keywords = asset_data['name'] + ' ' + asset_data['description'] + ' ' + ' '.join(asset_data['tags'])
        # if asset_data.get('canDownload') != 0:
        #     if context.view_layer.objects.active is not None and ui_props.asset_type == 'MODEL':
        #         aob = bpy.context.active_object
        #         op = layout.operator('scene.blenderkit_download', text='Replace Active Models')
        #         op.asset_type = ui_props.asset_type
        #         op.asset_index = ui_props.active_index
        #         op.model_location = aob.location
        #         op.model_rotation = aob.rotation_euler
        #         op.target_object = aob.name
        #         op.material_target_slot = aob.active_material_index
        #         op.replace = True
        #
        # wm = context.window_manager
        # profile = wm.get('bkit profile')
        # if profile is not None:
        #     # validation
        #     if utils.profile_is_validator():
        #         layout.label(text='Validation tools:')
        #         if asset_data['verificationStatus'] != 'uploaded':
        #             op = layout.operator('object.blenderkit_change_status', text='set Uploaded')
        #             op.asset_id = asset_data['id']
        #             op.state = 'uploaded'
        #         if asset_data['verificationStatus'] != 'validated':
        #             op = layout.operator('object.blenderkit_change_status', text='Validate')
        #             op.asset_id = asset_data['id']
        #             op.state = 'validated'
        #         if asset_data['verificationStatus'] != 'on_hold':
        #             op = layout.operator('object.blenderkit_change_status', text='Put on Hold')
        #             op.asset_id = asset_data['id']
        #             op.state = 'on_hold'
        #         if asset_data['verificationStatus'] != 'rejected':
        #             op = layout.operator('object.blenderkit_change_status', text='Reject')
        #             op.asset_id = asset_data['id']
        #             op.state = 'rejected'
        #
        #     if author_id == str(profile['user']['id']):
        #         layout.label(text='Management tools:')
        #         row = layout.row()
        #         row.operator_context = 'INVOKE_DEFAULT'
        #         op = row.operator('object.blenderkit_change_status', text='Delete')
        #         op.asset_id = asset_data['id']
        #         op.state = 'deleted'
            # else:
            #     #not an author - can rate
            #     draw_ratings(layout, context)
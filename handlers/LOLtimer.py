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

def timer_update():
    from ..utils import LOLutils as utils
    '''check for running and finished downloads and react. write progressbars too.'''
    if len(utils.download_threads) == 0:
        return None

    for threaddata in utils.download_threads:
        thread, asset, tcom = threaddata
        if tcom.finished:
            thread.stop()
            for d in tcom.passargs['downloaders']:
                utils.link_asset(bpy.context, asset, d['location'], d['rotation'])

            utils.download_threads.remove(threaddata)
            for area in bpy.data.window_managers['WinMan'].windows[0].screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

            return None
        for area in bpy.data.window_managers['WinMan'].windows[0].screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    return 0.5
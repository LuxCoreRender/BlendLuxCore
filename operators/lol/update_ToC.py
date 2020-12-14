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
from os.path import basename, dirname, join, isfile, splitext

from bpy.types import Operator
from ...utils.lol import utils as utils


class LOLUpdateTOC(Operator):
    bl_idname = 'scene.luxcore_ol_update_toc'
    bl_label = 'LuxCore Online Library Update Table of Contents from Server'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def description(cls, context, properties):
        return "Update table of contents from server"

    def execute(self, context):
        import urllib.request
        import json

        name = basename(dirname(dirname(dirname(__file__))))
        user_preferences = context.preferences.addons[name].preferences

        filepath = join(user_preferences.global_dir, 'assets_model_patreon.json')
        with urllib.request.urlopen(utils.LOL_HOST_URL + "/assets_model_patreon.json", timeout=60) as request:
            assets = json.load(request)

            with open(filepath, 'w') as file:
                file.write(json.dumps(assets, indent=2))

        filepath = join(user_preferences.global_dir, 'assets_model.json')
        with urllib.request.urlopen(utils.LOL_HOST_URL + "/assets_model.json", timeout=60) as request:
            assets = json.load(request)

            with open(filepath, 'w') as file:
                file.write(json.dumps(assets, indent=2))

        filepath = join(user_preferences.global_dir, 'assets_material.json')
        with urllib.request.urlopen(utils.LOL_HOST_URL + "/assets_material.json", timeout=60) as request:
            assets = json.load(request)

            with open(filepath, 'w') as file:
                file.write(json.dumps(assets, indent=2))

        return {'FINISHED'}
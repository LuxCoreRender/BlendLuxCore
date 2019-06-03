# from bl_ui.properties_particle import ParticleButtonsPanel
# from bpy.types import Panel
# from .. import utils
# from ..ui import icons
#
#
# class LUXCORE_HAIR_PT_hair(ParticleButtonsPanel, Panel):
#     bl_label = "LuxCore Hair Settings"
#     COMPAT_ENGINES = {"LUXCORE"}
#
#     @classmethod
#     def poll(cls, context):
#         psys = context.particle_system
#         if psys is None:
#             return False
#         if psys.settings is None:
#             return False
#         is_hair = psys.settings.type == "HAIR"
#         is_path = psys.settings.render_type == "PATH"
#         engine = context.scene.render.engine
#         return is_hair and is_path and engine == "LUXCORE"
#
#     def draw(self, context):
#         layout = self.layout
#         settings = context.particle_settings.luxcore.hair
#
#         # Note: we can always assume that obj.data has the attribute uv_textures,
#         # because objects that don't have it can't have a particle system in Blender.
#         # We can also assume that obj.data exists, because otherwise this panel is not visible.
#         obj = context.object
#
#         layout.prop(settings, "hair_size")
#
#         row = layout.row(align=True)
#         row.prop(settings, "root_width")
#         row.prop(settings, "tip_width")
#         row.prop(settings, "width_offset")
#
#         layout.prop(settings, "tesseltype")
#
#         if "adaptive" in settings.tesseltype:
#             row = layout.row(align=True)
#             row.prop(settings, "adaptive_maxdepth")
#             row.prop(settings, "adaptive_error")
#
#         if settings.tesseltype.startswith("solid"):
#             layout.prop(settings, "solid_sidecount")
#
#             row = layout.row()
#             row.prop(settings, "solid_capbottom")
#             row.prop(settings, "solid_captop")
#
#         layout.prop(settings, "copy_uv_coords")
#
#         # UV map selection
#         box = layout.box()
#         box.active = settings.copy_uv_coords or settings.export_color == "uv_texture_map"
#         col = box.column()
#         col.prop(settings, "use_active_uv_map")
#
#         if settings.use_active_uv_map:
#             if obj.data.uv_textures:
#                 active_uv = utils.find_active_uv(obj.data.uv_textures)
#                 if active_uv:
#                     row = col.row()
#                     row.label("UV Map:")
#                     row.label(active_uv.name, icon="GROUP_UVS")
#         else:
#             col.prop_search(settings, "uv_map_name",
#                             obj.data, "uv_textures",
#                             icon="GROUP_UVS")
#
#         if not obj.data.uv_textures:
#                 row = col.row()
#                 row.label("No UV map", icon=icons.WARNING)
#                 row.operator("mesh.uv_texture_add", icon=icons.ADD)
#
#         # Vertex color settings
#         box = layout.box()
#         box.prop(settings, "export_color")
#
#         if settings.export_color == "vertex_color":
#             col = box.column()
#             col.prop(settings, "use_active_vertex_color_layer")
#
#             if settings.use_active_vertex_color_layer:
#                 if obj.data.vertex_colors:
#                     active_vcol_layer = utils.find_active_vertex_color_layer(obj.data.vertex_colors)
#                     if active_vcol_layer:
#                         row = col.row()
#                         row.label("Vertex Colors:")
#                         row.label(active_vcol_layer.name, icon="GROUP_VCOL")
#             else:
#                 col.prop_search(settings, "vertex_color_layer_name",
#                                 obj.data, "vertex_colors",
#                                 icon="GROUP_VCOL", text="Vertex Colors")
#
#             if not obj.data.vertex_colors:
#                 row = col.row()
#                 row.label("No Vertex Colors", icon=icons.WARNING)
#                 row.operator("mesh.vertex_color_add", icon=icons.ADD)
#
#         elif settings.export_color == "uv_texture_map":
#             box.template_ID(settings, "image", open="image.open")
#             if settings.image:
#                 box.prop(settings, "gamma")
#             settings.image_user.draw(box, context.scene)
#
#         row = box.row()
#         row.prop(settings, "root_color")
#         row.prop(settings, "tip_color")
#
#         layout.prop(settings, "instancing")
#
#
# class LUXCORE_PARTICLE_PT_textures(ParticleButtonsPanel, Panel):
#     bl_label = "Textures"
#     bl_context = "particle"
#     bl_options = {'DEFAULT_CLOSED'}
#
#     @classmethod
#     def poll(cls, context):
#         psys = context.particle_system
#         engine = context.scene.render.engine
#         if psys is None:
#             return False
#         if psys.settings is None:
#             return False
#         return engine == "LUXCORE"
#
#     def draw(self, context):
#         layout = self.layout
#
#         psys = context.particle_system
#         part = psys.settings
#
#         row = layout.row()
#         row.template_list("TEXTURE_UL_texslots", "", part, "texture_slots", part, "active_texture_index", rows=2)
#
#         col = row.column(align=True)
#         col.operator("texture.slot_move", text="", icon='TRIA_UP').type = 'UP'
#         col.operator("texture.slot_move", text="", icon='TRIA_DOWN').type = 'DOWN'
#         col.menu("TEXTURE_MT_specials", icon='DOWNARROW_HLT', text="")
#
#         if not part.active_texture:
#             layout.template_ID(part, "active_texture", new="texture.new")
#         else:
#             slot = part.texture_slots[part.active_texture_index]
#             layout.template_ID(slot, "texture", new="texture.new")
#
#             row = layout.row()
#             op = row.operator("luxcore.switch_space_data_context", text="Show Texture Settings", icon="UI")
#             op.target = "TEXTURE"

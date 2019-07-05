from bl_ui.properties_texture import (
    TextureButtonsPanel, context_tex_datablock
)
import bpy
from bpy.types import Panel, Texture, ParticleSettings, Brush


class LUXCORE_TEXTURE_PT_context_texture(TextureButtonsPanel, Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout

        slot = getattr(context, "texture_slot", None)
        node = getattr(context, "texture_node", None)
        space = context.space_data
        tex = context.texture
        idblock = context_tex_datablock(context)
        pin_id = space.pin_id

        if not space.use_pin_id:
            row = layout.row(align=True)

            op = row.operator("luxcore.switch_texture_context", text="Particles", icon="PARTICLES")
            op.target = "PARTICLES"

            op = row.operator("luxcore.switch_texture_context", text="Other", icon="TEXTURE")
            op.target = "OTHER"

            pin_id = None

        if space.texture_context == 'OTHER':
            if not pin_id:
                row = layout.row()
                row.template_texture_user()
            user = context.texture_user
            if user or pin_id:
                layout.separator()

                row = layout.row()

                if pin_id:
                    row.template_ID(space, "pin_id")
                else:
                    propname = context.texture_user_property.identifier
                    row.template_ID(user, propname, new="texture.new")

                if tex:
                    split = layout.split(factor=0.2)
                    if tex.use_nodes:
                        if slot:
                            split.label(text="Output:")
                            split.prop(slot, "output_node", text="")
                    else:
                        split.label(text="Type:")
                        split.prop(tex, "type", text="")
            return

        tex_collection = (pin_id is None) and (node is None) and (not isinstance(idblock, Brush))

        if tex_collection:
            row = layout.row()

            row.template_list("TEXTURE_UL_texslots", "", idblock, "texture_slots",
                              idblock, "active_texture_index", rows=2)

            col = row.column(align=True)
            col.operator("texture.slot_move", text="", icon='TRIA_UP').type = 'UP'
            col.operator("texture.slot_move", text="", icon='TRIA_DOWN').type = 'DOWN'
            col.menu("TEXTURE_MT_specials", icon='DOWNARROW_HLT', text="")

        if tex_collection:
            layout.template_ID(idblock, "active_texture", new="texture.new")
        elif node:
            layout.template_ID(node, "texture", new="texture.new")
        elif idblock:
            layout.template_ID(idblock, "texture", new="texture.new")

        if pin_id:
            layout.template_ID(space, "pin_id")

        if tex:
            split = layout.split(factor=0.2)
            if tex.use_nodes:
                if slot:
                    split.label(text="Output:")
                    split.prop(slot, "output_node", text="")
            else:
                split.label(text="Type:")
                split.prop(tex, "type", text="")

def compatible_panels():
     panels = [
        # Texture panels
        # Used only for particles/brushes
        "TEXTURE_PT_preview",
        "TEXTURE_PT_colors",
        "TEXTURE_PT_influence",
        "TEXTURE_PT_mapping",

        # One panel per texture type
        "TEXTURE_PT_image",
        "TEXTURE_PT_image_mapping",
        "TEXTURE_PT_blend",
        "TEXTURE_PT_clouds",
        "TEXTURE_PT_distortednoise",
        "TEXTURE_PT_magic",
        "TEXTURE_PT_marble",
        "TEXTURE_PT_musgrave",
        "TEXTURE_PT_ocean",
        "TEXTURE_PT_pointdensity",
        "TEXTURE_PT_pointdensity_turbulence",
        "TEXTURE_PT_stucci",
        "TEXTURE_PT_voronoi",
        "TEXTURE_PT_voxeldata",
        "TEXTURE_PT_wood",
     ]
     types = bpy.types
     return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
   for panel in compatible_panels():
      panel.COMPAT_ENGINES.add("LUXCORE")    


def unregister():
   for panel in compatible_panels():
      panel.COMPAT_ENGINES.remove("LUXCORE")

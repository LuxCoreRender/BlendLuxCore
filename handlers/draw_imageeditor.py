import bpy
import blf

handle = None


def handler():
    context = bpy.context

    if context.scene.render.engine != "LUXCORE":
        return

    _denoiser_help_text(context)


def _denoiser_help_text(context):
    if not context.scene.luxcore.denoiser.enabled:
        return

    # Only show the help text if the toolshelf is not visible
    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            for space in area.spaces:
                if space == context.space_data:
                    # It is the current image editor
                    for region in area.regions:
                        # Note: when the tool region is hidden, it has width == 1
                        if region.type == "TOOLS" and region.width > 1:
                            # Toolshelf is visible, do not show the help text
                            return

    image_user = context.space_data.image_user
    layer_index = image_user.multilayer_layer
    render_layers = context.scene.render.layers

    if layer_index >= len(render_layers):
        return

    render_layer = render_layers[layer_index]

    # Combined is index 0, depth is index 1 if enabled, denoised pass is right behind them
    denoised_pass_index = 2 if render_layer.luxcore.aovs.depth else 1

    if image_user.multilayer_pass == denoised_pass_index:
        # From https://github.com/sftd/blender-addons-contrib/blob/master/render_time.py
        font_id = 0  # XXX, need to find out how best to get this. [sic]
        ui_scale = context.user_preferences.view.ui_scale
        dpi = round(72 * ui_scale)

        pos_y = 45 * ui_scale
        blf.position(font_id, 15, pos_y, 0)
        blf.size(font_id, 14, dpi)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 5, 0.0, 0.0, 0.0, 1.0)

        blf.draw(font_id, '← The denoiser controls are in the "LuxCore" category')
        pos_y -= 20 * ui_scale
        blf.position(font_id, 15, pos_y, 0)
        blf.draw(font_id, 'in the tool shelf, (press T)')

        # restore defaults
        blf.disable(font_id, blf.SHADOW)

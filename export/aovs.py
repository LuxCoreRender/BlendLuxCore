from ..bin import pyluxcore
from .. import utils

# set of channels that don"t use an HDR format
LDR_CHANNELS = {
    "RGB_IMAGEPIPELINE", "RGBA_IMAGEPIPELINE", "ALPHA", "MATERIAL_ID", "OBJECT_ID",
    "DIRECT_SHADOW_MASK", "INDIRECT_SHADOW_MASK", "MATERIAL_ID_MASK"
}


# Exported in config export
def convert(scene, context=None):
    try:
        prefix = "film.outputs."
        definitions = {}

        if scene.camera is None:
            # Can not work without a camera
            return pyluxcore.Properties()

        pipeline = scene.camera.data.luxcore.imagepipeline
        aovs = scene.luxcore.aovs

        # TODO make this generic
        # TODO correct filepaths

        index = 0

        # This output is always defined
        index = _add_output(definitions, "RGB_IMAGEPIPELINE", index)

        if pipeline.transparent_film:
            index = _add_output(definitions, "RGBA_IMAGEPIPELINE", index)

        if aovs.depth:
            index = _add_output(definitions, "DEPTH", index)

        if aovs.samplecount:
            index = _add_output(definitions, "SAMPLECOUNT", index)

        return utils.create_props(prefix, definitions)
    except Exception as error:
        msg = "Imagepipeline: %s" % error
        scene.luxcore.errorlog.add_warning(msg)
        return pyluxcore.Properties()


def _add_output(definitions, output_type_str, index):
    definitions[str(index) + ".type"] = output_type_str

    extension = ".png" if output_type_str in LDR_CHANNELS else ".exr"
    definitions[str(index) + ".filename"] = output_type_str + extension

    return index + 1

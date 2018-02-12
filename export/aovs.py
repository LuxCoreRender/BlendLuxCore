from ..bin import pyluxcore
from .. import utils

# set of channels that don"t use an HDR format
# LDR_channels = {
#     "RGB_IMAGEPIPELINE", "RGBA_IMAGEPIPELINE", "ALPHA", "MATERIAL_ID", "OBJECT_ID",
#     "DIRECT_SHADOW_MASK", "INDIRECT_SHADOW_MASK", "MATERIAL_ID_MASK"
# }


# Exported in config export
def convert(scene, context=None):
    try:
        prefix = "film.outputs."
        definitions = {}

        if scene.camera is None:
            # Can not work without a camera
            return pyluxcore.Properties()

        pipeline = scene.camera.data.luxcore.imagepipeline

        # TODO make this generic
        # TODO correct filepaths

        # This output is always defined
        definitions["0.type"] = "RGB_IMAGEPIPELINE"
        definitions["0.filename"] = "image.png"

        if pipeline.transparent_film:
            definitions["1.type"] = "RGBA_IMAGEPIPELINE"
            definitions["1.filename"] = "image2.png"


        definitions["1.type"] = "SAMPLECOUNT"
        definitions["1.filename"] = "samplecount.png"

        # definitions["1.type"] = "ALPHA"
        # definitions["1.filename"] = "alpha.png"

        return utils.create_props(prefix, definitions)
    except Exception as error:
        msg = "Imagepipeline: %s" % error
        scene.luxcore.errorlog.add_warning(msg)
        return pyluxcore.Properties()

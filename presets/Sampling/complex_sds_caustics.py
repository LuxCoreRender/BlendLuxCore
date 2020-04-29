import bpy
luxcore = bpy.context.scene.luxcore.config

luxcore.preset_version = 1
luxcore.engine = 'PATH'
luxcore.sampler = 'SOBOL'
luxcore.path.hybridbackforward_enable = True
luxcore.photongi.enabled = True
luxcore.photongi.caustic_enabled = True
luxcore.photongi.indirect_enabled = False
luxcore.envlight_cache.enabled = False
luxcore.dls_cache.enabled = False

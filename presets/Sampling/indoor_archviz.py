import bpy
luxcore = bpy.context.scene.luxcore.config

luxcore.preset_version = 1
luxcore.engine = 'PATH'
luxcore.sampler = 'SOBOL'
luxcore.path.hybridbackforward_enable = False
luxcore.photongi.enabled = True
luxcore.photongi.caustic_enabled = False
luxcore.photongi.indirect_enabled = True
luxcore.envlight_cache.enabled = True
luxcore.dls_cache.enabled = False

import bpy
from bpy.props import BoolProperty, PointerProperty, IntProperty, FloatVectorProperty
import pyluxcore
from ... import utils
from ...utils import node as utils_node
from ..output import LuxCoreNodeOutput, update_active, get_active_output
from ...ui import icons
from ...utils.errorlog import LuxCoreErrorLog

SHADOWCATCHER_DESC = (
    "Make this material transparent and only catch shadows on it. "
    "Used for compositing 3D objects into real-world footage. "
    "Remember to enable transparent film in camera settings"
)

ONLY_INFINITE_DESC = (
    "Only consider shadows of infinite lights (sky, HDRI, "
    "flat colored background) for the shadow catcher"
)

MATERIAL_ID_DESC = (
    "ID for Material ID AOV, if -1 is set a random ID is chosen. "
    "Note that the random IDs of LuxCore can be greater than 32767 "
    "(the ID Mask node in the compositor can't handle those numbers)"
)

SHADOW_COLOR_DESC = (
    "Black is the physically correct shadow color. Set it to white to "
    "let light pass through the material unobstructed, while keeping "
    "the appearance the same for anything but shadow rays (useful e.g. "
    "for thin sheets of glass as an alternative to architectural glass, "
    "to have refraction visible but let direct light pass through for "
    "better performance)"
)


class LuxCoreNodeMatOutput(LuxCoreNodeOutput, bpy.types.Node):
    """
    Material output node.
    This is where the export starts (if the output is active).
    """
    bl_label = "Material Output"
    bl_width_default = 220

    active: BoolProperty(name="Active", default=True, update=update_active)
    show_advanced: BoolProperty(name="Advanced", default=False, description="Show/hide advanced settings")
    id: IntProperty(update=utils_node.force_viewport_update, name="Material ID", default=-1, min=-1, soft_max=32767,
                     description=MATERIAL_ID_DESC)
    use_photongi: BoolProperty(name="Use PhotonGI Cache", default=True,
                                description="Disable for mirror-like surfaces like "
                                            "metal or glossy with low roughness")
    shadow_color: FloatVectorProperty(name="Shadow Color", subtype="COLOR", default=(0, 0, 0), min=0, max=1,
                                      update=utils_node.update_opengl_materials,
                                      description=SHADOW_COLOR_DESC)
    is_shadow_catcher: BoolProperty(update=utils_node.force_viewport_update, name="Shadow Catcher", default=False,
                                     description=SHADOWCATCHER_DESC)
    shadow_catcher_only_infinite: BoolProperty(update=utils_node.force_viewport_update, name="Only Infinite Lights", default=False,
                                                description=ONLY_INFINITE_DESC)
    is_holdout: BoolProperty(update=utils_node.force_viewport_update, name="Holdout", default=False,
                             description="Make film transparent on pixels where this material is directly visible")
    override_exclude: BoolProperty(name="Exclude from override",
                         default=False,
                         description="If an override material is defined, this will not be replaced.")

    def init(self, context):
        self.inputs.new("LuxCoreSocketMaterial", "Material")
        self.inputs.new("LuxCoreSocketVolume", "Interior Volume")
        self.inputs.new("LuxCoreSocketVolume", "Exterior Volume")
        self.inputs.new("LuxCoreSocketShape", "Shape")
        super().init(context)

    def copy(self, orig_node):
        super().copy(orig_node)

        node_tree = self.id_data
        if not node_tree:
            # Happens for example when copying from one node tree to another
            return

        # Copy the links to volumes
        for orig_input in orig_node.inputs:
            if orig_input.is_linked and orig_input.name in {"Interior Volume", "Exterior Volume"}:
                # We can not use orig_input.links because of a Blender exception
                links = utils_node.get_links(node_tree, orig_input)
                if links:
                    from_socket = links[0].from_socket
                    to_socket = self.inputs[orig_input.name]
                    node_tree.links.new(from_socket, to_socket)

    def draw_buttons(self, context, layout):
        icon = icons.EXPANDABLE_OPENED if self.show_advanced else icons.EXPANDABLE_CLOSED
        row = layout.row()
        super().draw_buttons(context, row)
        row.prop(self, "show_advanced", icon=icon, emboss=False)

        if not self.show_advanced:
            return

        box = layout.box()

        box.prop(self, "id")

        row = box.row()
        row.alignment = "LEFT"
        row.prop(self, "shadow_color", text="")
        row.label(text="Shadow Color")

        # PhotonGI
        photongi_enabled = context.scene.luxcore.config.photongi.enabled
        col = box.column()
        col.active = photongi_enabled
        if not photongi_enabled:
            col.label(text="PhotonGI Cache is not enabled", icon=icons.INFO)

        row = col.row()
        row.active = photongi_enabled
        row.prop(self, "use_photongi")

        # All of the options below only work with the Path engine, not with Bidir
        engine = context.scene.luxcore.config.engine
        col = box.column()
        col.active = engine == "PATH"
        if engine == "BIDIR":
            col.label(text="Not supported by Bidir engine:", icon=icons.INFO)

        # Holdout
        col.prop(self, "is_holdout")
        if self.is_holdout and engine == "PATH" and utils.is_valid_camera(context.scene.camera):
            pipeline = context.scene.camera.data.luxcore.imagepipeline
            if not pipeline.transparent_film:
                col.prop(pipeline, "transparent_film", text="Enable Transparent Film",
                            icon=icons.CAMERA, toggle=True)

        # Shadow catcher
        col.prop(self, "is_shadow_catcher")

        # Material override exclude
        col.prop(self, "override_exclude")

        if engine == "PATH" and self.is_shadow_catcher:
            col.prop(self, "shadow_catcher_only_infinite")
            # Some settings that should be used with shadow catcher
            if utils.is_valid_camera(context.scene.camera):
                pipeline = context.scene.camera.data.luxcore.imagepipeline
                if not pipeline.transparent_film:
                    col.prop(pipeline, "transparent_film", text="Enable Transparent Film",
                             icon=icons.CAMERA, toggle=True)
            if context.scene.world:
                luxcore_world = context.scene.world.luxcore
                is_ground_black = luxcore_world.ground_enable and tuple(luxcore_world.ground_color) == (0, 0, 0)

                if luxcore_world.light == "sky2" and not is_ground_black:
                    col.operator("luxcore.world_set_ground_black", icon=icons.WORLD)
                elif luxcore_world.light == "infinite" and not luxcore_world.sampleupperhemisphereonly:
                    col.prop(luxcore_world, "sampleupperhemisphereonly",
                             icon=icons.WORLD, toggle=True)

    def export(self, exporter, depsgraph, props, luxcore_name):
        prefix = "scene.materials." + luxcore_name + "."
        definitions = {}

        # Invalidate node cache
        # TODO have one global properties object so this is no longer necessary
        exporter.node_cache.clear()

        # We have to export volumes before the material definition because LuxCore properties
        # do not support forward declarations (the volume has to be already defined when it is
        # referenced in the material)
        interior_volume_name = self.inputs["Interior Volume"].export(exporter, depsgraph, props)
        exterior_volume_name = self.inputs["Exterior Volume"].export(exporter, depsgraph, props)

        # Export the material
        exported_name = self.inputs["Material"].export(exporter, depsgraph, props, luxcore_name)

        # Attach the volumes
        if interior_volume_name:
            definitions["volume.interior"] = interior_volume_name
        if exterior_volume_name:
            definitions["volume.exterior"] = exterior_volume_name

        if exported_name is None or exported_name != luxcore_name:
            # Export failed, e.g. because no node is linked or it's not a material node
            # Define a black material that signals an unconnected material socket
            self._convert_fallback(props, luxcore_name)

        if self.id != -1:
            # LuxCore only assigns a random ID if the ID is not set at all
            definitions["id"] = self.id
        definitions["shadowcatcher.enable"] = self.is_shadow_catcher
        definitions["shadowcatcher.onlyinfinitelights"] = self.shadow_catcher_only_infinite
        definitions["photongi.enable"] = self.use_photongi
        definitions["transparency.shadow"] = list(self.shadow_color)
        definitions["holdout.enable"] = self.is_holdout

        props.Set(utils.create_props(prefix, definitions))

    def _convert_volume(self, exporter, depsgraph, node_tree, props):
        if node_tree is None:
            return None

        try:
            luxcore_name = utils.get_luxcore_name(node_tree)
            active_output = get_active_output(node_tree)
            active_output.export(exporter, depsgraph, props, luxcore_name)
            return luxcore_name
        except Exception as error:
            msg = 'Node Tree "%s": %s' % (node_tree.name, error)
            LuxCoreErrorLog.add_warning(msg)
            import traceback
            traceback.print_exc()
            return None

    def _convert_fallback(self, props, luxcore_name):
        prefix = "scene.materials." + luxcore_name + "."
        props.Set(pyluxcore.Property(prefix + "type", "matte"))
        props.Set(pyluxcore.Property(prefix + "kd", [0, 0, 0]))

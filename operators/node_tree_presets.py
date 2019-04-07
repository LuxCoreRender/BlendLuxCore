from collections import OrderedDict
import bpy
from bpy.props import StringProperty, IntProperty
from mathutils import Color
from .. import utils
from .utils import poll_object, make_nodetree_name


def new_node(bl_idname, node_tree, previous_node, output=0, input=0):
    node = node_tree.nodes.new(bl_idname)
    node.location = (previous_node.location.x - 250, previous_node.location.y)
    node_tree.links.new(node.outputs[output], previous_node.inputs[input])
    return node


class LUXCORE_OT_preset_material(bpy.types.Operator):
    bl_idname = "luxcore.preset_material"
    bl_label = ""
    bl_description = "Add a pre-definied node setup"
    bl_options = {"UNDO"}

    basic_mapping = OrderedDict([
        ("Mix", "LuxCoreNodeMatMix"),
        ("Matte", "LuxCoreNodeMatMatte"),
        ("Glossy", "LuxCoreNodeMatGlossy2"),
        ("Glass", "LuxCoreNodeMatGlass"),
        ("Null (Transparent)", "LuxCoreNodeMatNull"),
        ("Metal", "LuxCoreNodeMatMetal"),
        ("Mirror", "LuxCoreNodeMatMirror"),
        ("Glossy Translucent", "LuxCoreNodeMatGlossyTranslucent"),
        ("Matte Translucent", "LuxCoreNodeMatMatteTranslucent"),
    ])

    preset = StringProperty()
    categories = OrderedDict([
        ("Basic", list(basic_mapping.keys())),
        ("Advanced", [
            "Smoke",
            "Fire and Smoke",
            "Colored Glass",
        ]),
    ])

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def _add_node_tree(self, name):
        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_material_nodes")
        node_tree.use_fake_user = True
        return node_tree

    def execute(self, context):
        mat = context.material
        obj = context.object

        if mat is None:
            # We need to create a material
            mat = bpy.data.materials.new(name="Material")

            # Attach the new material to the active object
            if obj.material_slots:
                obj.material_slots[obj.active_material_index].material = mat
            else:
                obj.data.materials.append(mat)

            # Flag the object for update, needed in viewport render
            obj.update_tag()

        # We have a material, but maybe it has no node tree attached
        node_tree = mat.luxcore.node_tree

        if node_tree is None:
            tree_name = make_nodetree_name(mat.name)
            node_tree = self._add_node_tree(tree_name)
            mat.luxcore.node_tree = node_tree
            # Flag the object for update, needed in viewport render
            obj.update_tag()

        nodes = node_tree.nodes
        output = None

        if len(nodes) == 1 and nodes[0].bl_idname == "LuxCoreNodeMatOutput":
            # The user deleted all nodes except the output.
            # Just use it instead of creating a new output.
            output = nodes[0]
        elif len(nodes) == 2:
            # It is probably a default material, replace the matte node with the preset
            matte = None

            for node in nodes:
                # Make sure it is an unchanged default matte node
                if (node.bl_idname == "LuxCoreNodeMatMatte"
                        and node.inputs["Diffuse Color"].default_value == Color((0.7, 0.7, 0.7))
                        and node.inputs["Sigma"].default_value == 0
                        and node.inputs["Opacity"].default_value == 1):
                    matte = node

                if node.bl_idname == "LuxCoreNodeMatOutput":
                    output = node

            if matte and output:
                nodes.remove(matte)
            else:
                # We were wrong - do not use this output
                output = None

        if output is None:
            # Add the new nodes below all other nodes
            # x location should be centered (average of other nodes x positions)
            # y location shoud be below all others
            location_x = 300
            location_y = 500

            for node in nodes:
                location_x = max(node.location.x, location_x)
                location_y = min(node.location.y, location_y)
                # De-select all nodes
                node.select = False

            # Create an output for the new nodes
            output = nodes.new("LuxCoreNodeMatOutput")
            output.location = (location_x, location_y - 300)
            output.select = False

        # Category: Basic
        if self.preset in self.basic_mapping:
            new_node(self.basic_mapping[self.preset], node_tree, output)
        # Category: Advanced
        elif self.preset == "Smoke":
            self._preset_smoke(obj, node_tree, output)
        elif self.preset == "Fire and Smoke":
            self._preset_fire_and_smoke(obj, node_tree, output)
        elif self.preset == "Colored Glass":
            self._preset_colored_glass(obj, node_tree, output)

        return {"FINISHED"}

    def _preset_smoke(self, obj, node_tree, output):
        # If it is not a smoke domain, create the material anyway, but warn the user
        is_smoke_domain = utils.find_smoke_domain_modifier(obj)

        new_node("LuxCoreNodeMatNull", node_tree, output)

        # We need a volume
        name = "Smoke Volume"
        vol_node_tree = bpy.data.node_groups.new(name=name, type="luxcore_volume_nodes")
        vol_nodes = vol_node_tree.nodes
        # Attach to output node
        volume_pointer = new_node("LuxCoreNodeTreePointer", node_tree, output, "Volume", "Interior Volume")
        volume_pointer.node_tree = vol_node_tree
        volume_pointer.location.y -= 100

        # Add volume nodes
        vol_output = vol_nodes.new("LuxCoreNodeVolOutput")
        vol_output.location = 300, 200

        heterogeneous = new_node("LuxCoreNodeVolHeterogeneous", vol_node_tree, vol_output)
        smoke_node = new_node("LuxCoreNodeTexSmoke", vol_node_tree, heterogeneous, 0, "Scattering")
        if is_smoke_domain:
            smoke_node.domain = obj
            heterogeneous.auto_step_settings = True
            heterogeneous.domain = obj
        smoke_node.source = "density"
        smoke_node.wrap = "black"
        # Use IOR of air (doesn't really matter)
        heterogeneous.inputs["IOR"].default_value = 1

        # A smoke material setup only makes sense on the smoke domain object
        if not is_smoke_domain:
            self.report({"ERROR"}, 'Object "%s" is not a smoke domain!' % obj.name)

    def _preset_fire_and_smoke(self, obj, node_tree, output):
        # If it is not a smoke domain, create the material anyway, but warn the user
        is_smoke_domain = utils.find_smoke_domain_modifier(obj)

        new_node("LuxCoreNodeMatNull", node_tree, output)

        # We need a volume
        name = "Fire and Smoke Volume"
        vol_node_tree = bpy.data.node_groups.new(name=name, type="luxcore_volume_nodes")
        vol_nodes = vol_node_tree.nodes
        # Attach to output node
        volume_pointer = new_node("LuxCoreNodeTreePointer", node_tree, output, "Volume", "Interior Volume")
        volume_pointer.node_tree = vol_node_tree
        volume_pointer.location.y -= 100

        # Add volume nodes
        vol_output = vol_nodes.new("LuxCoreNodeVolOutput")
        vol_output.location = 300, 200

        heterogeneous = new_node("LuxCoreNodeVolHeterogeneous", vol_node_tree, vol_output)
        # Scattering
        heterogeneous.inputs["Scattering Scale"].default_value = 10
        smoke_node = new_node("LuxCoreNodeTexSmoke", vol_node_tree, heterogeneous, 0, "Scattering")
        # Use IOR of air (doesn't really matter)
        heterogeneous.inputs["IOR"].default_value = 1

        if is_smoke_domain:
            smoke_node.domain = obj
            heterogeneous.auto_step_settings = True
            heterogeneous.domain = obj
        smoke_node.source = "density"
        smoke_node.wrap = "black"

        # Emission (fire) - these nodes need to be below the others
        fire_gain = new_node("LuxCoreNodeTexMath", vol_node_tree, heterogeneous, 0, "Emission")
        fire_gain.location.y -= 200
        fire_gain.mode = "scale"
        # Use a high gain value so the fire is visible with the default sky
        fire_gain.inputs["Value 2"].default_value = 100000

        # Colors for the flame
        fire_band = new_node("LuxCoreNodeTexBand", vol_node_tree, fire_gain, 0, "Value 1")
        fire_band.update_add(bpy.context)
        fire_band.update_add(bpy.context)
        fire_band.update_add(bpy.context)
        # Black
        fire_band.ramp_items[0].offset = 0
        fire_band.ramp_items[0].value = (0, 0, 0)
        # Dark red
        fire_band.ramp_items[1].offset = 0.25
        fire_band.ramp_items[1].value = (0.35, 0.03, 0)
        # Orange/yellow
        fire_band.ramp_items[2].offset = 0.8
        fire_band.ramp_items[2].value = (0.9, 0.4, 0)
        # Blue
        fire_band.ramp_items[3].offset = 0.95
        fire_band.ramp_items[3].value = (0.03, 0.3, 0.8)
        # White
        fire_band.ramp_items[4].offset = 1
        fire_band.ramp_items[4].value = (1, 1, 1)

        fire_node = new_node("LuxCoreNodeTexSmoke", vol_node_tree, fire_band, 0, "Amount")
        if is_smoke_domain:
            fire_node.domain = obj
        fire_node.source = "fire"
        fire_node.wrap = "black"

        # A smoke material setup only makes sense on the smoke domain object
        if not is_smoke_domain:
            self.report({"ERROR"}, 'Object "%s" is not a smoke domain!' % obj.name)

    def _preset_colored_glass(self, obj, node_tree, output):
        new_node("LuxCoreNodeMatGlass", node_tree, output)
        clear_vol = new_node("LuxCoreNodeVolClear", node_tree, output, 0, "Interior Volume")
        clear_vol.location.y -= 280
        clear_vol.inputs["Absorption"].default_value = (0.9, 0.1, 0.1)


class LUXCORE_MATERIAL_MT_node_tree_preset(bpy.types.Menu):
    bl_idname = "LUXCORE_MT_node_tree_preset"
    bl_label = "Add Node Tree Preset"
    bl_description = "Add a pre-definied node setup"

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        for category, presets in LUXCORE_OT_preset_material.categories.items():
            col = row.column()
            col.label(category)

            for preset in presets:
                op = col.operator("luxcore.preset_material", text=preset)
                op.preset = preset

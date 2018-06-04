import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, PointerProperty, EnumProperty
from .. import LuxCoreNodeTexture
from ...utils import ui as utils_ui
from ...utils import node as utils_node


datablock_icons = {
    'Mesh': "MESH_DATA",
    'Screen': "SPLITSCREEN",
    'NodeTree': "NODETREE",
    'ParticleSettings': "PARTICLE_DATA",
    'WindowManager': "NONE",
    'World': "WORLD",
    'Lattice': "LATTICE_DATA",
    'Object': "OBJECT_DATA",
    'Brush': "BRUSH_DATA",
    'Lamp': "LAMP_DATA",
    'Armature': "ARMATURE_DATA",
    'Image': "IMAGE_DATA",
    'Camera': "CAMERA_DATA",
    'Curve': "CURVE_DATA",
    'MetaBall': "META_DATA",
    'Material': "MATERIAL_DATA",
    'FreestyleLineStyle': "LINE_DATA",
    'Scene': "SCENE_DATA",
    'Speaker': "SPEAKER",
    'Text': "TEXT",
    'Texture': "TEXTURE_DATA",
}


def is_iterable(obj):
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def pad_or_cutoff(_list, length, pad_value=0):
    if len(_list) < length:
        return _list + [pad_value] * (length - len(_list))
    elif len(_list) > length:
        return _list[:length]
    else:
        return _list


def get_ID_subclasses():
    return [cls for cls in bpy.types.ID.__subclasses__()
            if cls not in {bpy.types.Library, bpy.types.Group, bpy.types.Sound}]


class LuxCorePropertyPointers(PropertyGroup):
    pass

for cls in get_ID_subclasses():
    setattr(LuxCorePropertyPointers, cls.__name__, PointerProperty(type=cls))


class LuxCoreNodeTexPropertyAccess(LuxCoreNodeTexture):
    bl_label = "PropertyAccess"

    def update_sockets(self, context):
        self.error = ""
        use_float_socket = True
        try:
            value, tex_type = self.convert_eval_result()

            if tex_type == "constfloat3":
                use_float_socket = False
        except Exception as error:
            self.error = str(error)

        value_output = self.outputs["Value"]
        color_output = self.outputs["Color"]
        was_value_enabled = value_output.enabled

        color_output.enabled = not use_float_socket
        value_output.enabled = use_float_socket

        utils_node.copy_links_after_socket_swap(value_output, color_output, was_value_enabled)

    pointers = PointerProperty(type=LuxCorePropertyPointers)
    datablock_types = [(cls.__name__, cls.__name__, "", datablock_icons[cls.__name__], i)
                       for i, cls in enumerate(get_ID_subclasses())]
    datablock_type = EnumProperty(name="Datablock Type", items=datablock_types, default="Object",
                                  update=update_sockets)
    attribute_path = StringProperty(name="Attribute", update=update_sockets)
    error = StringProperty(name="Error")

    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")
        self.outputs["Color"].enabled = False
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def draw_label(self):
        datablock = self.get_selected_datablock()
        if datablock and self.attribute_path:
            return datablock.name + "." + self.attribute_path
        else:
            return self.bl_label

    def draw_buttons(self, context, layout):
        layout.prop(self, "datablock_type")
        layout.prop(self.pointers, self.datablock_type)
        layout.prop(self, "attribute_path")
        if self.error:
            row = layout.row()
            row.label(self.error, icon="CANCEL")
            op = row.operator("luxcore.copy_error_to_clipboard", icon="COPYDOWN")
            op.message = self.error

    @staticmethod
    def parse_indices(index_str):
        indices = [int(s) for s in index_str.split(":")]
        len_indices = len(indices)

        if len_indices == 0:
            raise IndexError("No index given")
        elif len_indices == 1:
            start, end, step = indices[0], indices[0] + 1, 1
        elif len_indices == 2:
            start, end, step = indices[0], indices[1], 1
        elif len_indices == 3:
            start, end, step = indices
        else:
            raise IndexError("Too many indices (only start, end, step allowed)")
        return start, end, step, len_indices

    def get_selected_datablock(self):
        return getattr(self.pointers, self.datablock_type)

    def eval(self):
        datablock = self.get_selected_datablock()

        if datablock and self.attribute_path:
            value = datablock
            # Follow the chain of attributes
            for attrib in self.attribute_path.split("."):
                if "[" in attrib:
                    # Indexed access of an iterable
                    iter_attrib, index_str = attrib.split("[")
                    index_str = index_str.replace("]", "")
                    start, end, step, len_indices = self.parse_indices(index_str)

                    iterable = getattr(value, iter_attrib)
                    if not is_iterable(iterable):
                        raise TypeError(iter_attrib + " is not iterable")

                    if len_indices == 1:
                        # Some iterables in Blender don't have slicing support,
                        # so we don't use it if we don't have to
                        value = iterable[start]
                    else:
                        value = iterable[start:end:step]
                else:
                    value = getattr(value, attrib)
            return value
        return 0

    def convert_eval_result(self):
        value = self.eval()

        try:
            # Check if it is iterable (Color, Vector etc.)
            as_list = pad_or_cutoff(list(value), length=3)
            return as_list, "constfloat3"
        except TypeError:
            # Not iterable
            return value, "constfloat1"

    def sub_export(self, exporter, props, luxcore_name=None):
        self.error = ""
        utils_ui.tag_region_for_redraw(bpy.context, "NODE_EDITOR", "WINDOW")

        value = None
        try:
            value, tex_type = self.convert_eval_result()
            definitions = {
                "type": tex_type,
                "value": value,
            }

            return self.create_props(props, definitions, luxcore_name)
        except Exception as error:
            print("Error during evaluation of", self.bl_label, "node in tree", self.id_data)
            if value:
                print("The evaluation result was:", value)
            import traceback
            traceback.print_exc()

            self.error = str(error)
            utils_ui.tag_region_for_redraw(bpy.context, "NODE_EDITOR", "WINDOW")

            definitions = {
                "type": "constfloat1",
                "value": 0,
            }

            return self.create_props(props, definitions, luxcore_name)


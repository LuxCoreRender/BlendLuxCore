from bpy.props import StringProperty, BoolProperty
from .. import LuxCoreNodeTexture
from ...ui import icons


def convert(string):
    separated = string.strip().split(",")
    return [float(elem) for elem in separated]


class LuxCoreNodeTexIrregularData(LuxCoreNodeTexture):
    bl_label = "Irregular Data"

    equal_length = BoolProperty(default=True)
    error = StringProperty()

    def update_data(self, context):
        try:
            wavelengths_converted = convert(self.wavelengths)
            data_converted = convert(self.data)
            self.equal_length = len(wavelengths_converted) == len(data_converted)
            self.error = ""
        except ValueError as error:
            print(error)
            self.error = str(error)

    wavelengths = StringProperty(name="", default="580.0, 620.0, 660.0", update=update_data,
                                 description="Comma-separated list of values")
    data = StringProperty(name="", default="0.0, 0.000015, 0.0", update=update_data,
                          description="Comma-separated list of values")

    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.label("Wavelengths:")
        layout.prop(self, "wavelengths")
        layout.label("Data:")
        layout.prop(self, "data")

        if not self.equal_length:
            layout.label("Both lists need the same number of values!", icon=icons.ERROR)

        if self.error:
            layout.label(self.error, icon=icons.ERROR)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "irregulardata",
            "wavelengths": convert(self.wavelengths),
            "data": convert(self.data),
        }
        return self.create_props(props, definitions, luxcore_name)

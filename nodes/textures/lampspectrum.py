import bpy
from bpy.props import EnumProperty
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node

CATEGORY_ITEMS = [
    ("Natural", "Natural", "", 0),
    ("Incandescent", "Incandescent", "", 1),
    ("Fluorescent", "Fluorescent", "", 2),
    ("High_Pressure_Mercury", "High Pressure Mercury", "", 3),
    ("Sodium_Discharge", "Sodium Discharge", "", 4),
    ("Metal_Halide", "Metal Halide", "", 5),
    ("Diode", "Diode", "", 6),
    ("Spectral", "Spectral", "", 7),
    ("Glow_Discharge", "Glow Discharge", "", 8),
    ("Molecular", "Molecular", "", 9),
    ("Fluorescence", "Fluorescence", "", 10),
    ("Various", "Various", "", 11),
    ("BlacklightUV", "Blacklight/UV", "", 12),
    ("Mercury_UV", "Mercury UV", "", 13),
    ("AbsorptionMixed", "Absorption/Mixed", "", 14),
]

NATURAL_ITEMS = [
    ("Daylight", "Natural Daylight", "", 0)
]

INCANDESCENT_ITEMS = [
    ("Candle", "Paraffin Candle Flame", "", 0),
    ("Incandescent1", "Generic 7W Incandescent Lamp", "", 1),
    ("Incandescent2", "PHILIPS [Argenta] 200W Incandescent Lamp", "", 2),
    ("Welsbach", "Welsbach Gas Mantle (modern, without Thorium)", "", 3),
    ("AntiInsect", "Incandescent Anti-Insect Lamp", "", 4),
]

FLOURESCENT_ITEMS = [
    ("FLD2", "PHILIPS [TL-D 30W/55] Regular Daylight Fluorescent", "", 0),
    ("FL37K", "Sylvania [F4T5 4W] Regular Warm White Fluorescent", "", 1),
    ("CFL27K", "OSRAM [DULUXSTAR 21W/827] Regular Compact Triphosphor Fluorescent", "", 2),
    ("CFL4K", "Cold Cathode Warm White CFL Triphosphor Fluorescent", "", 3),
    ("CFL6K", "NARVA [COLOURLUX plus daylight 20W/860] Daylight CFL Triphosphor Fluorescent", "", 4),
    ("GroLux", "Sylvania [GroLux] Fluorescent Aquarium/Plant Lamp", "", 5),
    ("LCDS", "Laptop LCD Screen", "", 6),
    ("FLAV8K", "PHILIPS [ActiViva] \"Natural\" Triphosphor Fluorescent", "", 7),
    ("FLAV17K", "PHILIPS [ActiViva] \"Active\" Triphosphor Fluorescent", "", 8)
]

HIGH_PRESSURE_MERCURY_ITEMS = [
    ("HPM2", "OSRAM [HQA 80W] Clear HPM Lamp", "", 0),
    ("HPMFL1", "PHILIPS [HPL 125W] HPM Lamp with improved color", "", 1),
    ("HPMFL2", "OSRAM [HQL 80W] HPM Lamp with improved warm deluxe color", "", 2),
    ("HPMSB", "PHILIPS [ML 160W] Self-Ballasted HPM Vapor Lamp", "", 3),
    ("HPMSBFL", "NARVA [160W] Self-ballasted HPM Vapor Lamp", "", 4),
]

SODIUM_DISCHARGE_ITEMS = [
    ("SS1", "Regular High Pressure Sodium Lamp, warmup after 5-7 sec", "", 0),
    ("SS2", "Regular High Pressure Sodium Lamp, warmup after 10-12 sec", "", 1),
    ("LPS", "SOX Low Pressure Sodium Discharge Lamp", "", 2),
    ("MPS", "Medium Pressure Sodium Discharge Lamp, warmup after ~35 sec", "", 3),
    ("HPS", "GE [Lucalox 35W] High Pressure Sodium Lamp", "", 4),
    ("SHPS", "PHILIPS [SDW-T 100W] Super High Pressure White Sodium Lamp", "", 5),
]

METAL_HALIDE_ITEMS = [
    ("MHN", "PHILIPS [HPI-T 400W] MH Lamp with Mercury, Sodium, Thallium and Indium iodides", "", 0),
    ("MHWWD", "OSRAM [HQI-TS 75W/WDL] Metal Halide lamp with Mercury, sodium, thallium, indium and tin iodides, from", "", 1),
    ("MHSc", "GE [MVR325IUWM 325 Watt I-Line Multi-Vapor Metal Halide - Clear Watt Miser] MH Lamp with Mercury, Sodium and Scandium iodides", "", 2),
    ("MHD", "OSRAM [HQI-T 400W/D] MH Lamp with Mercury, Thallium, Dysprosium, Holmium, Thulium and Caesium iodides", "", 3),
    ("FeCo", "PHILIPS Diazo MH Lamp with Mercury, iron and cobalt iodides", "", 4),
    ("GaPb", "Sylvania Diazo MH Lamp with Mercury, gallium and lead iodides", "", 5),
    ("BLAU", "OSRAM [HQI-T 400W/Blau] Blue colored MH Lamp with Mercury and indium iodides", "", 6),
    ("PLANTA", "RADIUM [HRI-T 400W/Planta] Plant growing MH Lamp with Mercury, indium and sodium iodides", "", 7),
    ("GRUN", "OSRAM [HQI-T 400W/Grun] Green colored MH Lamp with Mercury and thallium iodides", "", 8),
]

DIODE_ITEMS = [
    ("LEDB", "Regular High Brightness Blue LED", "", 0),
    ("RedLaser", "Monochromatic emission from a Red Laser diode", "", 1),
    ("GreenLaser", "Monochromatic emission from a Green Laser diode", "", 2),
]

SPECTRAL_ITEMS = [
    ("XeI", "PHILIPS Spectral Xenon Lamp - Continuous Xenon low pressure thermionic discharge", "", 0),
    ("Rb", "PHILIPS spectral Rubidium Lamp - Continuous Rubidium low pressure thermionic discharge", "", 1),
    ("Cd", "PHILIPS spectral Cadmium Lamp - Continuous Cadmium low pressure thermionic discharge", "", 2),
    ("Zn", "PHILIPS spectral zinc Lamp - Continuous Zinc low pressure thermionic discharge", "", 3),
]

GLOW_DISCHARGE_ITEMS = [
    ("NeKrFL", "Neon and Krypton glow discharge and green phosphor (night-lights/indicators)", "", 0),
    ("NeXeFL1", "Neon and Xenon glow discharge and green phosphor (night-lights/indicators)", "", 1),
    ("NeXeFL2", "Neon and Xenon glow discharge and blue phosphor (night-lights/indicators)", "", 2),
    ("Ar", "Argon glow discharge", "", 3),
    ("HPMFL2Glow", "Self-ballasted High Pressure Mercury Vapor Lamp, with yttrium vanadate phosphate fluorescent phosphors, \
    in glow discharge mode", "", 4),
]

MOLECULAR_ITEMS = [
    ("Butane", "Butane Gas Flame", "", 0),
    ("Alcohol", "Alcohol Flame", "", 1),
]

FLUORECENCE_ITEMS = [
    ("BLP", "Print quality A4 Xerox paper wrapped around a blacklight Lamp", "", 0),
    ("BLNG", "Neon green dye, bombarded with black light", "", 1),
    ("TV", "Regular Modern Color TV CRT", "", 2),
]

VARIOUS_ITEMS = [
    ("Xe", "Stroboscopic flash. Xenon I, likely II and perhaps III", "", 0),
    ("CarbonArc", "Carbon Arc Spectrum", "", 1),
    ("HPX", "OSRAM [XBO 75W/2] Short Arc Xenon Lamp", "", 2),
]

BLACKLIGHT_ITEMS = [
    ("LPM2", "Sylvania [G8T5 8W] Germicidal lamp", "", 0),
    ("FLBLB", "Sylvania [F6T5/BLB 8W] Black light blue fluorescent", "", 1),
    ("FLBL", "Sylvania [Blacklite 350 F8W/BL350] Black Light fluorescent", "", 2),
]

MERCURY_UV_ITEMS = [
    ("UVA", "The near visible UVA emissions from a high pressure Mercury clear lamp", "", 0),
]

ABSORPTION_ITEMS = [
    ("HPMFLCobaltGlass", "High Pressure Mercury Warm Deluxe light ([1.4.3]) absorbed through blue Cobalt glass", "", 0),
    ("CobaltGlass", "Incandescent light ([1.2.3]) absorbed through blue Cobalt glass", "", 1),
    ("HPMFLCL42053", "High Pressure Mercury Warm Deluxe light ([1.4.3]) absorbed through ciel dye #42053", "", 2),
    ("CL42053", "Incandescent light ([1.2.3]) absorbed through ciel dye #42053", "", 3),
    ("HPMFLRedGlass", "High Pressure Mercury Warm Deluxe light ([1.4.3]) absorbed through red glass", "", 4),
    ("RedGlass", "Incandescent light ([1.2.3]) absorbed through red glass.m", "", 5),
    ("OliveOil", "Incandescent light ([1.2.3]) absorbed through olive oil. ", "", 6),
]


class LuxCoreNodeTexLampSpectrum(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Lamp Spectrum"
    bl_width_default = 310

    lamp_category: EnumProperty(update=utils_node.force_viewport_update, name="Lamp Category", description="Lamp Preset Category", items=CATEGORY_ITEMS,
                                        default="Natural")

    lamp_spectrum_natural: EnumProperty(update=utils_node.force_viewport_update, name="Natural Preset", description="Natural Preset", items=NATURAL_ITEMS,
                                        default="Daylight")
    lamp_spectrum_incandescent: EnumProperty(update=utils_node.force_viewport_update, name="Incandescent Preset", description="Incandescent Preset", items=INCANDESCENT_ITEMS,
                                        default="Candle")
    lamp_spectrum_fluorescent: EnumProperty(update=utils_node.force_viewport_update, name="Fluorescent Preset", description="Fluorescent Preset", items=FLOURESCENT_ITEMS,
                                        default="FLD2")
    lamp_spectrum_high_pressure_mercury: EnumProperty(update=utils_node.force_viewport_update, name="High Pressure Mercury Preset", description="High Pressure Mercury Preset", items=HIGH_PRESSURE_MERCURY_ITEMS,
                                        default="HPM2")
    lamp_spectrum_sodium_discharge: EnumProperty(update=utils_node.force_viewport_update, name="Sodium Discharge Preset", description="Sodium Discharge Preset", items=SODIUM_DISCHARGE_ITEMS,
                                        default="SS1")
    lamp_spectrum_metal_halide: EnumProperty(update=utils_node.force_viewport_update, name="Metal Halide Preset", description="Metal Halide Preset", items=METAL_HALIDE_ITEMS,
                                        default="MHN")
    lamp_spectrum_diode: EnumProperty(update=utils_node.force_viewport_update, name="Diode Preset", description="Diode Preset", items=DIODE_ITEMS,
                                        default="LEDB")
    lamp_spectrum_spectral: EnumProperty(update=utils_node.force_viewport_update, name="Spectral", description="Spectral Preset", items=SPECTRAL_ITEMS,
                                       default="XeI")
    lamp_spectrum_glow_discharge: EnumProperty(update=utils_node.force_viewport_update, name="Glow Discharge Preset", description="low Discharge Preset", items=GLOW_DISCHARGE_ITEMS,
                                        default="NeKrFL")
    lamp_spectrum_molecular: EnumProperty(update=utils_node.force_viewport_update, name="Molecular Preset", description="Molecular Preset", items=MOLECULAR_ITEMS,
                                        default="Butane")
    lamp_spectrum_fluorescence: EnumProperty(update=utils_node.force_viewport_update, name="Flourecence Preset", description="Flourecence Preset", items=FLUORECENCE_ITEMS,
                                        default="BLP")
    lamp_spectrum_various: EnumProperty(update=utils_node.force_viewport_update, name="Various Preset", description="Various Preset", items=VARIOUS_ITEMS,
                                        default="Xe")
    lamp_spectrum_blacklight: EnumProperty(update=utils_node.force_viewport_update, name="Blacklight Preset", description="Blacklight Preset", items=BLACKLIGHT_ITEMS,
                                        default="LPM2")
    lamp_spectrum_mercury_uv: EnumProperty(update=utils_node.force_viewport_update, name="Mercury/UV Preset", description="Mercury/UV Preset", items=MERCURY_UV_ITEMS,
                                        default="UVA")
    lamp_spectrum_absorption: EnumProperty(update=utils_node.force_viewport_update, name="Absorption/Mixed Preset", description="bsorption/Mixed Preset", items=ABSORPTION_ITEMS,
                                        default="HPMFLCobaltGlass")

    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "lamp_category")
        
        if self.lamp_category == "Natural":
            layout.prop(self, "lamp_spectrum_natural")
        elif self.lamp_category == "Incandescent":
            layout.prop(self, "lamp_spectrum_incandescent")
        elif self.lamp_category == "Fluorescent":
            layout.prop(self, "lamp_spectrum_fluorescent")            
        elif self.lamp_category == "High_Pressure_Mercury":
            layout.prop(self, "lamp_spectrum_high_pressure_mercury")            
        elif self.lamp_category == "Sodium_Discharge":
            layout.prop(self, "lamp_spectrum_sodium_discharge")            
        elif self.lamp_category == "Metal_Halide":
            layout.prop(self, "lamp_spectrum_metal_halide")            
        elif self.lamp_category == "Diode":            
            layout.prop(self, "lamp_spectrum_diode")            
        elif self.lamp_category == "Spectral":
            layout.prop(self, "lamp_spectrum_spectral")            
        elif self.lamp_category == "Glow_Discharge":
            layout.prop(self, "lamp_spectrum_glow_discharge")            
        elif self.lamp_category == "Molecular":
            layout.prop(self, "lamp_spectrum_molecular")            
        elif self.lamp_category == "Fluorescence":
            layout.prop(self, "lamp_spectrum_fluorescence")            
        elif self.lamp_category == "Various":
            layout.prop(self, "lamp_spectrum_various")            
        elif self.lamp_category == "BlacklightUV":
            layout.prop(self, "lamp_spectrum_blacklight")            
        elif self.lamp_category == "Mercury_UV":
            layout.prop(self, "lamp_spectrum_mercury_uv")            
        elif self.lamp_category == "AbsorptionMixed":
            layout.prop(self, "lamp_spectrum_absorption")
        else:
            raise NotImplementedError("Unknown lamp category")
    
    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        if self.lamp_category == "Natural":
            spectrum_name = self.lamp_spectrum_natural
        elif self.lamp_category == "Incandescent":
            spectrum_name = self.lamp_spectrum_incandescent
        elif self.lamp_category == "Fluorescent":
            spectrum_name = self.lamp_spectrum_fluorescent
        elif self.lamp_category == "High Pressure Mercury":
            spectrum_name = self.lamp_spectrum_high_pressure_mercury
        elif self.lamp_category == "Sodium Discharge":
            spectrum_name = self.lamp_spectrum_sodium_discharge
        elif self.lamp_category == "Metal Halide":
            spectrum_name = self.lamp_spectrum_metal_halide
        elif self.lamp_category == "Diode":            
            spectrum_name = self.lamp_spectrum_diode
        elif self.lamp_category == "Spectral":
            spectrum_name = self.lamp_spectrum_spectral
        elif self.lamp_category == "Glow Discharge":
            spectrum_name = self.lamp_spectrum_glow_discharge
        elif self.lamp_category == "Molecular":
            spectrum_name = self.lamp_spectrum_molecular
        elif self.lamp_category == "Fluorescence":
            spectrum_name = self.lamp_spectrum_fluorescence
        elif self.lamp_category == "Various":
            spectrum_name = self.lamp_spectrum_various
        elif self.lamp_category == "Blacklight/UV":
            spectrum_name = self.lamp_spectrum_blacklight
        elif self.lamp_category == "Mercury UV":
            spectrum_name = self.lamp_spectrum_mercury_uv
        elif self.lamp_category == "Absorption/Mixed":
            spectrum_name = self.lamp_spectrum_absorption
        else:
            raise NotImplementedError("Unknown lamp category")

        definitions = {
            "type": "lampspectrum",
            "name": spectrum_name,
        }       
        
        return self.create_props(props, definitions, luxcore_name)

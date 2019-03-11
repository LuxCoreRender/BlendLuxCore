from bpy.props import EnumProperty
from .. import LuxCoreNodeTexture

CATEGORY_ITEMS = [
    ("Natural", "Natural", ""),
    ("Incandescent", "Incandescent", ""),
    ("Fluorescent", "Fluorescent", ""),
    ("High Pressure Mercury", "High Pressure Mercury", ""),
    ("Sodium Discharge", "Sodium Discharge", ""),
    ("Metal Halide", "Metal Halide", ""),
    ("Diode", "Diode", ""),
    ("Spectral", "Spectral", ""),
    ("Glow Discharge", "Glow Discharge", ""),
    ("Molecular", "Molecular", ""),
    ("Fluorescence", "Fluorescence", ""),
    ("Various", "Various", ""),
    ("Blacklight/UV", "Blacklight/UV", ""),
    ("Mercury UV", "Mercury UV", ""),
    ("Absorption/Mixed", "Absorption/Mixed", ""),
]

NATURAL_ITEMS = [
    ("Daylight", "Natural Daylight", "")
]

INCANDESCENT_ITEMS = [
    ("Candle", "Paraffin Candle Flame", ""),
    ("Incandescent1", "Generic 7W Incandescent Lamp", ""),
    ("Incandescent2", "PHILIPS [Argenta] 200W Incandescent Lamp", ""),
    ("Welsbach", "Welsbach Gas Mantle (modern, without Thorium)", ""),
    ("AntiInsect", "Incandescent Anti-Insect Lamp", ""),
]

FLOURESCENT_ITEMS = [
    ("FLD2", "PHILIPS [TL-D 30W/55] Regular Daylight Fluorescent", ""),
    ("FL37K", "Sylvania [F4T5 4W] Regular Warm White Fluorescent", ""),
    ("CFL27K", "OSRAM [DULUXSTAR 21W/827] Regular Compact Triphosphor Fluorescent", ""),
    ("CFL4K", "Cold Cathode Warm White CFL Triphosphor Fluorescent", ""),
    ("CFL6K", "NARVA [COLOURLUX plus daylight 20W/860] Daylight CFL Triphosphor Fluorescent", ""),
    ("GroLux", "Sylvania [GroLux] Fluorescent Aquarium/Plant Lamp", ""),
    ("LCDS", "Laptop LCD Screen", ""),
    ("FLAV8K", "PHILIPS [ActiViva] \"Natural\" Triphosphor Fluorescent", ""),
    ("FLAV17K", "PHILIPS [ActiViva] \"Active\" Triphosphor Fluorescent", "")
]

HIGH_PRESSURE_MERCURY_ITEMS = [
    ("HPM2", "OSRAM [HQA 80W] Clear HPM Lamp", ""),
    ("HPMFL1", "PHILIPS [HPL 125W] HPM Lamp with improved color", ""),
    ("HPMFL2", "OSRAM [HQL 80W] HPM Lamp with improved warm deluxe color", ""),
    ("HPMSB", "PHILIPS [ML 160W] Self-Ballasted HPM Vapor Lamp", ""),
    ("HPMSBFL", "NARVA [160W] Self-ballasted HPM Vapor Lamp", ""),
]

SODIUM_DISCHARGE_ITEMS = [
    ("SS1", "Regular High Pressure Sodium Lamp, warmup after 5-7 sec", ""),
    ("SS2", "Regular High Pressure Sodium Lamp, warmup after 10-12 sec", ""),
    ("LPS", "SOX Low Pressure Sodium Discharge Lamp", ""),
    ("MPS", "Medium Pressure Sodium Discharge Lamp, warmup after ~35 sec", ""),
    ("HPS", "GE [Lucalox 35W] High Pressure Sodium Lamp", ""),
    ("SHPS", "PHILIPS [SDW-T 100W] Super High Pressure White Sodium Lamp", ""),
]

METAL_HALIDE_ITEMS = [
    ("MHN", "PHILIPS [HPI-T 400W] MH Lamp with Mercury, Sodium, Thallium and Indium iodides", ""),
    ("MHWWD", "OSRAM [HQI-TS 75W/WDL] Metal Halide lamp with Mercury, sodium, thallium, indium and tin iodides, from", ""),
    ("MHSc", "GE [MVR325IUWM 325 Watt I-Line Multi-Vapor Metal Halide - Clear Watt Miser] MH Lamp with Mercury, Sodium and Scandium iodides", ""),
    ("MHD", "OSRAM [HQI-T 400W/D] MH Lamp with Mercury, Thallium, Dysprosium, Holmium, Thulium and Caesium iodides", ""),
    ("FeCo", "PHILIPS Diazo MH Lamp with Mercury, iron and cobalt iodides", ""),
    ("GaPb", "Sylvania Diazo MH Lamp with Mercury, gallium and lead iodides", ""),
    ("BLAU", "OSRAM [HQI-T 400W/Blau] Blue colored MH Lamp with Mercury and indium iodides", ""),
    ("PLANTA", "RADIUM [HRI-T 400W/Planta] Plant growing MH Lamp with Mercury, indium and sodium iodides", ""),
    ("GRUN", "OSRAM [HQI-T 400W/Grun] Green colored MH Lamp with Mercury and thallium iodides", ""),
]

DIODE_ITEMS = [
    ("LEDB", "Regular High Brightness Blue LED", ""),
    ("RedLaser", "Monochromatic emission from a Red Laser diode", ""),
    ("GreenLaser", "Monochromatic emission from a Green Laser diode", ""),
]

SPECTRAL_ITEMS = [
    ("XeI", "PHILIPS Spectral Xenon Lamp - Continuous Xenon low pressure thermionic discharge", ""),
    ("Rb", "PHILIPS spectral Rubidium Lamp - Continuous Rubidium low pressure thermionic discharge", ""),
    ("Cd", "PHILIPS spectral Cadmium Lamp - Continuous Cadmium low pressure thermionic discharge", ""),
    ("Zn", "PHILIPS spectral zinc Lamp - Continuous Zinc low pressure thermionic discharge", ""),
]

GLOW_DISCHARGE_ITEMS = [
    ("NeKrFL", "Neon and Krypton glow discharge and green phosphor (night-lights/indicators)", ""),
    ("NeXeFL1", "Neon and Xenon glow discharge and green phosphor (night-lights/indicators)", ""),
    ("NeXeFL2", "Neon and Xenon glow discharge and blue phosphor (night-lights/indicators)", ""),
    ("Ar", "Argon glow discharge", ""),
    ("HPMFL2Glow", "Self-ballasted High Pressure Mercury Vapor Lamp, with yttrium vanadate phosphate fluorescent phosphors, \
    in glow discharge mode", ""),
]

MOLECULAR_ITEMS = [
    ("Butane", "Butane Gas Flame", ""),
    ("Alcohol", "Alcohol Flame", ""),
]

FLUORECENCE_ITEMS = [
    ("BLP", "Print quality A4 Xerox paper wrapped around a blacklight Lamp", ""),
    ("BLNG", "Neon green dye, bombarded with black light", ""),
    ("TV", "Regular Modern Color TV CRT", ""),
]

VARIOUS_ITEMS = [
    ("Xe", "Stroboscopic flash. Xenon I, likely II and perhaps III", ""),
    ("CarbonArc", "Carbon Arc Spectrum", ""),
    ("HPX", "OSRAM [XBO 75W/2] Short Arc Xenon Lamp", ""),
]

BLACKLIGHT_ITEMS = [
    ("LPM2", "Sylvania [G8T5 8W] Germicidal lamp", ""),
    ("FLBLB", "Sylvania [F6T5/BLB 8W] Black light blue fluorescent", ""),
    # (HPMBL", "PHILIPS [HPW 125W] High Pressure Mercury Black Light", ""),
    ("FLBL", "Sylvania [Blacklite 350 F8W/BL350] Black Light fluorescent", ""),
]

MERCURY_UV_ITEMS = [
    ("UVA", "The near visible UVA emissions from a high pressure Mercury clear lamp", ""),
]

ABSORPTION_ITEMS = [
    ("HPMFLCobaltGlass", "High Pressure Mercury Warm Deluxe light ([1.4.3]) absorbed through blue Cobalt glass", ""),
    ("CobaltGlass", "Incandescent light ([1.2.3]) absorbed through blue Cobalt glass", ""),
    ("HPMFLCL42053", "High Pressure Mercury Warm Deluxe light ([1.4.3]) absorbed through ciel dye #42053", ""),
    ("CL42053", "Incandescent light ([1.2.3]) absorbed through ciel dye #42053", ""),
    ("HPMFLRedGlass", "High Pressure Mercury Warm Deluxe light ([1.4.3]) absorbed through red glass", ""),
    ("RedGlass", "Incandescent light ([1.2.3]) absorbed through red glass.m", ""),
    ("OliveOil", "Incandescent light ([1.2.3]) absorbed through olive oil. ", ""),
]


class LuxCoreNodeTexLampSpectrum(LuxCoreNodeTexture):
    bl_label = "Lamp Spectrum"
    bl_width_default = 310

    lamp_category = EnumProperty(name="Lamp Category", description="Lamp Preset Category", items=CATEGORY_ITEMS,
                                        default="Natural")

    lamp_spectrum_natural = EnumProperty(name="Natural Preset", description="Natural Preset", items=NATURAL_ITEMS,
                                        default="Daylight")
    lamp_spectrum_incandescent = EnumProperty(name="Incandescent Preset", description="Incandescent Preset", items=INCANDESCENT_ITEMS,
                                        default="Candle")
    lamp_spectrum_fluorescent = EnumProperty(name="Fluorescent Preset", description="Fluorescent Preset", items=FLOURESCENT_ITEMS,
                                        default="FLD2")
    lamp_spectrum_high_pressure_mercury = EnumProperty(name="High Pressure Mercury Preset", description="High Pressure Mercury Preset", items=HIGH_PRESSURE_MERCURY_ITEMS,
                                        default="HPM2")
    lamp_spectrum_sodium_discharge = EnumProperty(name="Sodium Discharge Preset", description="Sodium Discharge Preset", items=SODIUM_DISCHARGE_ITEMS,
                                        default="SS1")
    lamp_spectrum_metal_halide = EnumProperty(name="Metal Halide Preset", description="Metal Halide Preset", items=METAL_HALIDE_ITEMS,
                                        default="MHN")
    lamp_spectrum_diode = EnumProperty(name="Diode Preset", description="Diode Preset", items=DIODE_ITEMS,
                                        default="LEDB")
    lamp_spectrum_spectral = EnumProperty(name="Spectral", description="Spectral Preset", items=SPECTRAL_ITEMS,
                                       default="XeI")
    lamp_spectrum_glow_discharge = EnumProperty(name="Glow Discharge Preset", description="low Discharge Preset", items=GLOW_DISCHARGE_ITEMS,
                                        default="NeKrFL")
    lamp_spectrum_molecular = EnumProperty(name="Molecular Preset", description="Molecular Preset", items=MOLECULAR_ITEMS,
                                        default="Butane")
    lamp_spectrum_fluorescence = EnumProperty(name="Flourecence Preset", description="Flourecence Preset", items=FLUORECENCE_ITEMS,
                                        default="BLP")
    lamp_spectrum_various = EnumProperty(name="Various Preset", description="Various Preset", items=VARIOUS_ITEMS,
                                        default="Xe")
    lamp_spectrum_blacklight = EnumProperty(name="Blacklight Preset", description="Blacklight Preset", items=BLACKLIGHT_ITEMS,
                                        default="LPM2")
    lamp_spectrum_mercury_uv = EnumProperty(name="Mercury/UV Preset", description="Mercury/UV Preset", items=MERCURY_UV_ITEMS,
                                        default="UVA")
    lamp_spectrum_absorption = EnumProperty(name="Absorption/Mixed Preset", description="bsorption/Mixed Preset", items=ABSORPTION_ITEMS,
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
        elif self.lamp_category == "High Pressure Mercury":
            layout.prop(self, "lamp_spectrum_high_pressure_mercury")            
        elif self.lamp_category == "Sodium Discharge":
            layout.prop(self, "lamp_spectrum_sodium_discharge")            
        elif self.lamp_category == "Metal Halide":
            layout.prop(self, "lamp_spectrum_metal_halide")            
        elif self.lamp_category == "Diode":            
            layout.prop(self, "lamp_spectrum_diode")            
        elif self.lamp_category == "Spectral":
            layout.prop(self, "lamp_spectrum_spectral")            
        elif self.lamp_category == "Glow Discharge":
            layout.prop(self, "lamp_spectrum_glow_discharge")            
        elif self.lamp_category == "Molecular":
            layout.prop(self, "lamp_spectrum_molecular")            
        elif self.lamp_category == "Fluorescence":
            layout.prop(self, "lamp_spectrum_fluorescence")            
        elif self.lamp_category == "Various":
            layout.prop(self, "lamp_spectrum_various")            
        elif self.lamp_category == "Blacklight/UV":
            layout.prop(self, "lamp_spectrum_blacklight")            
        elif self.lamp_category == "Mercury UV":
            layout.prop(self, "lamp_spectrum_mercury_uv")            
        elif self.lamp_category == "Absorption/Mixed":
            layout.prop(self, "lamp_spectrum_absorption")
        else:
            raise NotImplementedError("Unknown lamp category")
    
    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
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

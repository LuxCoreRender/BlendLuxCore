import bpy
import os
import mathutils
from math import radians
from bpy.props import EnumProperty, PointerProperty, StringProperty, IntProperty, BoolProperty
from ..base import LuxCoreNodeTexture
from ... import utils
from ...bin import pyluxcore

from ...ui import icons
from ...utils.errorlog import LuxCoreErrorLog


FIRST_FRAME_DESC = (
    "Raise this value if you want to leave out frames from the beginning of the sequence"
)

LAST_FRAME_DESC = (
    "Lower this value if you want to leave out frames from the end of the sequence"
)

class LuxCoreNodeTexOpenVDB(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "OpenVDB File"
    bl_width_default = 200

    def update_file_path(self, context):
        if self.file_path != '':
            frame = context.scene.frame_current
            indexed_filepaths = utils.openVDB_sequence_resolve_all(self.file_path)
            self.first_frame = 1
            if indexed_filepaths:
                first_index, first_path = indexed_filepaths[0]
                frame_count = len(indexed_filepaths)
                self.last_frame = frame_count
                self.frame_offset = -first_index + 1
            else:
                self.last_frame = 1
                self.frame_offset = 0

            # Copy current output sockets for reconnection after update
            old_sockets = {}
            for e in self.outputs:
                links = []
                for link in e.links:
                    links.append(link.to_socket)
                old_sockets[e.name] = links.copy()

            self.outputs.clear()
            names = pyluxcore.GetOpenVDBGridNames(bpy.path.abspath(self.file_path))
            for n in names:
                bbox, gridtype = pyluxcore.GetOpenVDBGridInfo(bpy.path.abspath(self.file_path), n)

                if gridtype == "float":
                    self.outputs.new("LuxCoreSocketFloatPositive", n)
                else:
                    self.outputs.new("LuxCoreSocketColor", n)

                if n == "density" or len(names) == 1:
                    self.nx = abs(bbox[0] - bbox[3])
                    self.ny = abs(bbox[1] - bbox[4])
                    self.nz = abs(bbox[2] - bbox[5])

            # Reconnect output sockets with same name as previously connected ones
            for e in self.outputs:
                try:
                    node_tree = self.id_data
                    for link in old_sockets[e.name]:
                        node_tree.links.new(e, link)
                except KeyError:
                    pass

    def update_domain(self, context):
        if self.domain != None and utils.find_smoke_domain_modifier(self.domain) and self.use_internal_cachefiles:
            depsgraph = context.evaluated_depsgraph_get()
            frame = depsgraph.scene_eval.frame_current
            domain_eval = self.domain.evaluated_get(depsgraph)
            self.file_path = self.get_cachefile_name(domain_eval, frame, 0)
            self.creator = "blender"


    def get_cachefile_name(self, domain, frame, index):
        mod = utils.find_smoke_domain_modifier(self.domain)
        file_format = mod.domain_settings.cache_file_format

        frame_start = mod.domain_settings.point_cache.point_caches[0].frame_start
        frame_end = mod.domain_settings.point_cache.point_caches[0].frame_end

        if file_format == 'OPENVDB':
            ext = "vdb"
        else:
            ext = "bphys"

        p = mod.domain_settings.point_cache.point_caches[index]
        print('name:', p.name)

        id = p.name
        if id == '':
            # Calculate cache ID
            for i in range(len(domain.name)):
                id = id + str(hex(ord(domain.name[i])))[-2:]

        if p.use_library_path:
            print("use_library_path has not been implemented yet")

        if p.use_external:
            folder = p.filepath
            filename = '%s_%06d_%02d.%s' % (id, utils.clamp(frame, frame_start, frame_end), p.index, ext)
            filepath = folder + '\\' + filename
        else:
            folder = os.path.dirname(bpy.data.filepath)
            subfolder = 'blendcache_' + os.path.split(bpy.data.filepath)[1].split(".")[0]
            filename = '%s_%06d_%02d.%s' % (id, utils.clamp(frame, frame_start, frame_end), p.index, ext)
            filepath = folder + '\\' + subfolder + '\\' + filename

        print('use_disk_cache:', p.use_disk_cache)
        print('filepath:', bpy.path.abspath(filepath))

        return filepath

    domain: PointerProperty(name="Smoke domain", type=bpy.types.Object, update=update_domain)

    precision_items = [
        ("byte", "Byte", "Only 1 byte per value. Required memory is 1/2 of Half and 1/4 of Float", 0),
        ("half", "Half", "2 bytes per value. Required memory is 1/2 of Float, but 2 times the size of Byte", 1),
        (
        "float", "Float", "4 bytes per value. Required memory is 2 times the size of half and 4 times the size of Byte",
        2),
    ]

    precision: EnumProperty(name="Precision", items=precision_items, default="half",
                            description="How many bytes to use per value. The floating point precision "
                                        "increases/decreases when more/less bytes are used. Low floating "
                                        "point precision can lead to artifacts when the smoke resolution is low")

    file_path: StringProperty(name="OpenVDB File", subtype="FILE_PATH", update=update_file_path, description="Specify path to OpenVDB file. Only portable if a relative path is used")

    first_frame: IntProperty(name="First Frame", default=1, min=1,  description=FIRST_FRAME_DESC)
    last_frame: IntProperty(name="Last Frame", default=2, min=1, description=LAST_FRAME_DESC)
    # TODO description?
    frame_offset: IntProperty(name="Offset", default=0)

    use_internal_cachefiles: BoolProperty(name="Use Internal Cache Files", default=True, update=update_domain)
    use_bbox_offset: BoolProperty(name="Use Bounding Box Offset", default=True)

    creator_items = [
        ("blender", "Blender File", "The OpenVDB files were generated with Blender.", 0),
        ("houdini", "Houdini File", "The OpenVDB files were generated with Houdini.", 1),
        ("other", "other File", "The OpenVDB files were generated with other programm.", 2),
    ]
    creator: EnumProperty(name="Creator", items=creator_items, default="blender",
                            description="The 3D programm which generated the OpenVDB files.")


    nx: IntProperty(name="nx", description="Number of cells in x direction", default=32)
    ny: IntProperty(name="ny", description="Number of cells in y direction", default=32)
    nz: IntProperty(name="nz", description="Number of cells in z direction", default=32)

    gridtype: StringProperty(name="Grid type", description="data type of grid data")


    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        if self.file_path != "":
            names = []
            self.outputs.clear()
            names = pyluxcore.GetOpenVDBGridNames(bpy.path.abspath(self.file_path))
            for n in names:
                bbox, gridtype = pyluxcore.GetOpenVDBGridInfo(bpy.path.abspath(self.file_path), n)

                if gridtype[0] == "float":
                    self.outputs.new("LuxCoreSocketFloatPositive", n)
                else:
                    self.outputs.new("LuxCoreSocketColor", n)


    def draw_buttons(self, context, layout):
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "domain")


        if self.domain:
            col = layout.column(align=True)
            if utils.find_smoke_domain_modifier(self.domain):
                col.prop(self, "use_internal_cachefiles")
            col = layout.column(align=True)
            col.enabled = not self.use_internal_cachefiles
            col.prop(self, "creator")

            if utils.find_smoke_domain_modifier(self.domain) and self.use_internal_cachefiles:
                mod = utils.find_smoke_domain_modifier(self.domain)
                settings = mod.domain_settings
                col = layout.column(align=True)
                col.enabled = False
                col.prop(settings.point_cache.point_caches[0], "frame_start", text="Start frame")
                col.prop(settings.point_cache.point_caches[0], "frame_end", text="End frame")
            else:
                col.prop(self, "file_path")
                col = layout.column(align=True)
                col.prop(self, "first_frame")
                col.prop(self, "last_frame")
                col.prop(self, "frame_offset")

                layout.prop(self, "use_bbox_offset")

                col = layout.column(align=True)
                col.prop(self, "nx")
                col.prop(self, "ny")
                col.prop(self, "nz")

        else:
            layout.label(text="Select the smoke domain object", icon=icons.WARNING)


    def get_frame(self, scene):
        frame = scene.frame_current + self.frame_offset
        frame = utils.clamp(frame, self.first_frame, self.last_frame)
        return frame

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        if not self.domain or self.file_path == "":
            error = "No Domain object selected."
            msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
            LuxCoreErrorLog.add_warning(msg)

            definitions = {
                "type": "constfloat3",
                "value": [0, 0, 0],
            }
            return self.create_props(props, definitions, luxcore_name)

        domain_eval = self.domain.evaluated_get(depsgraph)
        frame = depsgraph.scene_eval.frame_current

        #Get correct data file according to current frame
        smoke_domain_mod = utils.find_smoke_domain_modifier(domain_eval)
        if self.use_internal_cachefiles:
            if smoke_domain_mod:
                settings = smoke_domain_mod.domain_settings
                frame_start = settings.point_cache.point_caches[0].frame_start
                frame_end = settings.point_cache.point_caches[0].frame_end

                file_path = self.get_cachefile_name(domain_eval, utils.clamp(frame, frame_start, frame_end), 0)
        else:
            file_path = self.file_path
            indexed_filepaths = utils.openVDB_sequence_resolve_all(self.file_path)
            if len(indexed_filepaths) > 1:
                index, file_path = indexed_filepaths[utils.clamp(frame, self.first_frame, self.last_frame)-1]

        #Get transformation of domain bounding box, local center is lower bounding box corner
        scale = domain_eval.dimensions
        translate = domain_eval.matrix_world @ mathutils.Vector([v for v in domain_eval.bound_box[0]])
        rotate = domain_eval.rotation_euler

        # create a location matrix
        tex_loc = mathutils.Matrix.Translation(translate)

        # create a rotation matrix
        tex_rot0 = mathutils.Matrix.Rotation(rotate[0], 4, 'X')
        tex_rot1 = mathutils.Matrix.Rotation(rotate[1], 4, 'Y')
        tex_rot2 = mathutils.Matrix.Rotation(rotate[2], 4, 'Z')
        tex_rot = tex_rot2 @ tex_rot1 @ tex_rot0

        # create an scale matrix
        tex_sca = mathutils.Matrix()
        tex_sca[0][0] = scale[0] # X
        tex_sca[1][1] = scale[1] # Y
        tex_sca[2][2] = scale[2] # Z

        # Combine transformations of domain bounding box
        obmat = tex_loc @ tex_rot @ tex_sca

        # Get grid information from OpenVDB file, i.e. grid bounding box and type
        bbox, gridtype = pyluxcore.GetOpenVDBGridInfo(bpy.path.abspath(file_path), output_socket.name)

        fluidmat = mathutils.Matrix()
        houdini_transform = mathutils.Matrix()

        nx = abs(bbox[0] - bbox[3])
        ny = abs(bbox[1] - bbox[4])
        nz = abs(bbox[2] - bbox[5])

        if smoke_domain_mod and self.use_internal_cachefiles:
            amplify = 1
            use_high_resolution = smoke_domain_mod.domain_settings.use_high_resolution

            if use_high_resolution and output_socket.name not in {"density_low", "flame_low", "fuel_low",
                                                                  "react_low", "velocity", "heat"}:
                # Note: Velocity and heat data is always low-resolution. (Comment from Cycles source code)
                amplify = smoke_domain_mod.domain_settings.amplify + 1

            resolution = mathutils.Vector((0, 0, 0))
            cell_size = mathutils.Vector((0, 0, 0))

            for i in range(3):
                resolution[i] = smoke_domain_mod.domain_settings.domain_resolution[i] * amplify
                cell_size[i] = smoke_domain_mod.domain_settings.cell_size[i] * 1/amplify

            # Construct fluid matrix
            fluidmat[0][0] = nx/resolution[0]
            fluidmat[1][1] = ny/resolution[1]
            fluidmat[2][2] = nz/resolution[2]

            fluidmat = fluidmat @ mathutils.Matrix.Translation(mathutils.Vector((bbox[0]/nx,
                                                                                    bbox[1]/ny,
                                                                                    bbox[2]/nz))+ 0.5*cell_size)
        else:
            if self.creator != "other":
                fluidmat[0][0] = nx/self.nx
                fluidmat[1][1] = ny/self.ny
                fluidmat[2][2] = nz/self.nz

            if self.creator == "houdini":
                # As y is Up in Houdini, switch y and z axis to fit coordonate frame of Blender
                houdini_transform = mathutils.Matrix.Translation((0.5, 0.5, 0.5)) @ mathutils.Matrix.Rotation(radians(90.0), 4, 'X') \
                                    @ mathutils.Matrix.Translation((-0.5, -0.5, -0.5))

        # LuxCore normalize grid dimensions to [0..1] range, if the dimension of the bounding box of different grids
        # in one file is different the bounding box offset, e.g. lower corner of the box has to be considered,
        # e.g. in smoke / flame simulations

        if self.use_bbox_offset:
            fluidmat = fluidmat @ mathutils.Matrix.Translation(mathutils.Vector((bbox[0]/nx,
                                                                                    bbox[1]/ny,
                                                                                    bbox[2]/nz)))


        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, depsgraph, props)
        mapping_type = 'globalmapping3d'

        # combine transformations
        matrix_transformation = utils.matrix_to_list(transformation @ obmat @ fluidmat @ houdini_transform,
                                                     scene=exporter.scene,
                                                     apply_worldscale=True,
                                                     invert=True)


        definitions = {
            "type": "densitygrid",
            "wrap": "black",
            "storage": self.precision,
            "nx": nx,
            "ny": ny,
            "nz": nz,
            "openvdb.file": bpy.path.abspath(file_path),
            "openvdb.grid": output_socket.name,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": matrix_transformation,
        }

        return self.create_props(props, definitions, luxcore_name)

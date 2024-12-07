import bpy
import os
import mathutils
from math import radians
from bpy.props import EnumProperty, PointerProperty, StringProperty, IntProperty, BoolProperty
from ..base import LuxCoreNodeTexture
from ... import utils
import pyluxcore

from ...ui import icons
from ...utils.errorlog import LuxCoreErrorLog
from ...handlers import frame_change_pre


FIRST_FRAME_DESC = (
    "Raise this value if you want to leave out frames from the beginning of the sequence"
)

LAST_FRAME_DESC = (
    "Lower this value if you want to leave out frames from the end of the sequence"
)

HIGH_RES_DESC= (
    "The high resolution amplification used for generating the smoke data"
)

class LuxCoreNodeTexOpenVDB(LuxCoreNodeTexture, bpy.types.Node):
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
            self.has_high_resolution = False
            self.use_high_resolution = False

            for name in names:
                # metadata is only exposed for blender cache files, its a list with the following data
                # [min_bbox, max_bbox, res, min_res, max_res, base_res, obmat, obj_shift_f]
                creator, bbox, bBox_world, transform, gridtype, metadata = pyluxcore.GetOpenVDBGridInfo(bpy.path.abspath(self.file_path), name)
                if creator == "Blender/Smoke":
                    if "low" in name:
                        self.has_high_resolution = True
                        self.use_high_resolution = True
                        continue

                    self.creator = "blender"
                    base_res = metadata[5]

                    self.nx = base_res[0]
                    self.ny = base_res[1]
                    self.nz = base_res[2]

                elif "Houdini" in creator:
                    self.creator = "houdini"
                    if name == "density" or len(names) == 1:
                        self.nx = abs(bbox[0] - bbox[3])
                        self.ny = abs(bbox[1] - bbox[4])
                        self.nz = abs(bbox[2] - bbox[5])
                else:
                    self.creator = "other"
                    if name == "density" or len(names) == 1:
                        self.nx = abs(bbox[0] - bbox[3])
                        self.ny = abs(bbox[1] - bbox[4])
                        self.nz = abs(bbox[2] - bbox[5])

                if gridtype == "float":
                    self.outputs.new("LuxCoreSocketFloatPositive", name)
                else:
                    self.outputs.new("LuxCoreSocketColor", name)

            # Reconnect output sockets with same name as previously connected ones
            for output in self.outputs:
                try:
                    node_tree = self.id_data
                    for link in old_sockets[output.name]:
                        node_tree.links.new(output, link)
                except KeyError:
                    pass

    def update_use_internal(self, context):
        if self.domain != None and utils.find_smoke_domain_modifier(self.domain) and self.use_internal_cachefiles:
            depsgraph = context.evaluated_depsgraph_get()
            frame = depsgraph.scene_eval.frame_current
            domain_eval = self.domain.evaluated_get(depsgraph)
            self.file_path = self.get_cachefile_name(domain_eval, frame, 0)
            self.creator = "blender"
            self.use_bbox_offset = True

    def update_domain(self, context):
        self.use_internal_cachefiles = False
        if self.domain != None and utils.find_smoke_domain_modifier(self.domain):
            depsgraph = context.evaluated_depsgraph_get()
            frame = depsgraph.scene_eval.frame_current
            domain_eval = self.domain.evaluated_get(depsgraph)
            self.file_path = self.get_cachefile_name(domain_eval, frame, 0)
            self.creator = "blender"
            self.use_internal_cachefiles = True

    def get_cachefile_name(self, domain, frame, index):
        mod = utils.find_smoke_domain_modifier(self.domain)
        file_format = mod.domain_settings.cache_file_format

        frame_start = mod.domain_settings.point_cache.frame_start
        frame_end = mod.domain_settings.point_cache.frame_end

        if file_format == 'OPENVDB':
            ext = "vdb"
        else:
            ext = "bphys"

        point_cache = mod.domain_settings.point_cache

        id = point_cache.name
        if id == '':
            # Calculate cache ID
            for i in range(len(domain.name)):
                id = id + str(hex(ord(domain.name[i])))[-2:]

        if point_cache.use_library_path:
            print("use_library_path has not been implemented yet")

        if point_cache.use_external:
            folder = point_cache.filepath
            filename = '%s_%06d_%02d.%s' % (id, utils.clamp(frame, frame_start, frame_end), point_cache.index, ext)
            filepath = folder + '/' + filename
        else:
            folder = os.path.dirname(bpy.data.filepath)
            subfolder = 'blendcache_' + os.path.split(bpy.data.filepath)[1].split(".")[0]
            filename = '%s_%06d_%02d.%s' % (id, utils.clamp(frame, frame_start, frame_end), point_cache.index, ext)
            filepath = folder + '/' + subfolder + '/' + filename

        return filepath

    domain: PointerProperty(name="Smoke domain", type=bpy.types.Object, update=update_domain)

    precision_items = [
        ("byte", "Byte", "Only 1 byte per value. Required memory is 1/2 of Half and 1/4 of Float", 0),
        ("half", "Half", "2 bytes per value. Required memory is 1/2 of Float, but 2 times the size of Byte", 1),
        (
        "float", "Float", "4 bytes per value. Required memory is 2 times the size of half and 4 times the size of Byte",
        2),
    ]
    creator_items = [
        ("blender", "Blender File", "The OpenVDB files were generated with Blender", 0),
        ("houdini", "Houdini File", "The OpenVDB files were generated with Houdini", 1),
        ("other", "other File", "The OpenVDB files were generated with other programm", 2),
    ]

    precision: EnumProperty(name="Precision", items=precision_items, default="half",
                            description="How many bytes to use per value. The floating point precision "
                                        "increases/decreases when more/less bytes are used. Low floating "
                                        "point precision can lead to artifacts when the smoke resolution is low")

    amplify: IntProperty(name="High Resolution Devisions", default=1, min=1,  description=HIGH_RES_DESC)
    file_path: StringProperty(name="OpenVDB File", subtype="FILE_PATH", update=update_file_path, description="Specify path to OpenVDB file. Only portable if a relative path is used")
    first_frame: IntProperty(name="First Frame", default=1, min=1,  description=FIRST_FRAME_DESC)
    last_frame: IntProperty(name="Last Frame", default=2, min=1, description=LAST_FRAME_DESC)
    # TODO description?
    frame_offset: IntProperty(name="Offset", default=0)

    use_internal_cachefiles: BoolProperty(name="Use Internal Cache Files", default=True, update=update_use_internal)
    use_high_resolution: BoolProperty(name="Use High Resolution", default=True)
    has_high_resolution: BoolProperty(name="Has High Resolution", default=False)
    use_bbox_offset: BoolProperty(name="Use Bounding Box Offset", default=True)
    creator: EnumProperty(name="Creator", items=creator_items, default="blender",
                            description="The 3D programm which generated the OpenVDB files")

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
            for name in names:
                creator, bbox, bBox_world, transform, gridtype, metadata = pyluxcore.GetOpenVDBGridInfo(bpy.path.abspath(self.file_path), name)

                if gridtype[0] == "float":
                    self.outputs.new("LuxCoreSocketFloatPositive", name)
                else:
                    self.outputs.new("LuxCoreSocketColor", name)


    def draw_buttons(self, context, layout):
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "domain")

        if self.domain:
            col = layout.column(align=True)
            mod = utils.find_smoke_domain_modifier(self.domain)
            if mod:
                col.prop(self, "use_internal_cachefiles")

                if not self.use_internal_cachefiles and mod.domain_settings.use_adaptive_domain:
                    col = layout.column(align=True)
                    col.label(text="Internal Cache found!", icon=icons.WARNING)
            col = layout.column(align=True)
            col.enabled = True
            col.prop(self, "creator")
            layout.prop(self, "precision")

            if utils.find_smoke_domain_modifier(self.domain) and self.use_internal_cachefiles:
                col.enabled = False
                mod = utils.find_smoke_domain_modifier(self.domain)
                settings = mod.domain_settings
                col = layout.column(align=True)
                col.enabled = False
                col.prop(settings.point_cache.point_caches[0], "frame_start", text="Start frame")
                col.prop(settings.point_cache.point_caches[0], "frame_end", text="End frame")
            else:
                col = layout.column(align=True)
                col.prop(self, "file_path")
                col = layout.column(align=True)
                col.prop(self, "first_frame")
                col.prop(self, "last_frame")
                col.prop(self, "frame_offset")

                if self.creator == "blender":
                    layout.prop(self, "use_bbox_offset")
                    if self.has_high_resolution:
                        layout.prop(self, "use_high_resolution")

                    col = layout.column(align=True)
                    if self.use_high_resolution:
                        col.prop(self, "amplify")
                    col = layout.column(align=True)
                    col.enabled = False
                else:
                    col = layout.column(align=True)
                    col.enabled = True
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
        smoke_domain_mod = utils.find_smoke_domain_modifier(domain_eval)
        frame = depsgraph.scene_eval.frame_current

        #Get correct data file according to current frame
        file_path = self.file_path
        if self.use_internal_cachefiles:
            if smoke_domain_mod:
                settings = smoke_domain_mod.domain_settings
                frame_start = settings.point_cache.frame_start
                frame_end = settings.point_cache.frame_end

                file_path = self.get_cachefile_name(domain_eval, utils.clamp(frame, frame_start, frame_end), 0)
                if frame_end > frame_start:
                    frame_change_pre.have_to_check_node_trees = True
        else:
            indexed_filepaths = utils.openVDB_sequence_resolve_all(self.file_path)
            if len(indexed_filepaths) > 1:
                index, file_path = indexed_filepaths[utils.clamp(frame, self.first_frame, self.last_frame)-1]
                if self.last_frame > self.first_frame:
                    frame_change_pre.have_to_check_node_trees = True

        #Get transformation of domain bounding box, local center is lower bounding box corner
        scale = domain_eval.dimensions

        translate = domain_eval.matrix_world @ mathutils.Vector(domain_eval.bound_box[0][:])
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

        grid_name = output_socket.name
        if self.has_high_resolution and not self.use_high_resolution and grid_name in \
                {"density", "flame", "fuel", "heat", "react"}:
            grid_name = grid_name + "_low"

        # Get grid information from OpenVDB file, i.e. grid bounding box and type
        creator, bbox, bBox_world, trans_matrix, gridtype, metadata = pyluxcore.GetOpenVDBGridInfo(bpy.path.abspath(file_path), grid_name)

        ovdb_transform = mathutils.Matrix(
            (trans_matrix[0:4], trans_matrix[4:8], trans_matrix[8:12], trans_matrix[12:16])).transposed()

        ovdb_trans = ovdb_transform.translation
        ovdb = mathutils.Matrix()

        ovdb[0][0] = abs(bBox_world[0] - bBox_world[3])
        ovdb[1][1] = abs(bBox_world[1] - bBox_world[4])
        ovdb[2][2] = abs(bBox_world[2] - bBox_world[5])

        ovdb[0][3] = ovdb_trans[0]
        ovdb[1][3] = ovdb_trans[1]
        ovdb[2][3] = ovdb_trans[2]

        fluidmat = mathutils.Matrix()
        houdini_transform = mathutils.Matrix()

        nx = abs(bbox[0] - bbox[3])
        ny = abs(bbox[1] - bbox[4])
        nz = abs(bbox[2] - bbox[5])

        if smoke_domain_mod and self.use_internal_cachefiles:
            amplify = 1
            use_high_resolution = smoke_domain_mod.domain_settings.use_high_resolution

            if use_high_resolution and grid_name not in {"density_low", "flame_low", "fuel_low",
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

            fluidmat = fluidmat @ mathutils.Matrix.Translation(mathutils.Vector(0.5 * cell_size))
        else:
            if self.creator == "blender":
                base_res = metadata[5]
                resolution = metadata[2]
                min_res = metadata[3]
                max_res = metadata[4]
                min_bbox = mathutils.Vector(metadata[0])
                max_bbox = mathutils.Vector(metadata[1])

                amp = 1
                if self.use_high_resolution:
                    amp = self.amplify + 1
                resolution[0] *= amp
                resolution[1] *= amp
                resolution[2] *= amp

                base_res[0] *= amp
                base_res[1] *= amp
                base_res[2] *= amp

                min_res[0] *= amp
                min_res[1] *= amp
                min_res[2] *= amp

                max_res[0] *= amp
                max_res[1] *= amp
                max_res[2] *= amp

                cell_size = ((max_bbox[0] - min_bbox[0]) / base_res[0],
                             (max_bbox[1] - min_bbox[1]) / base_res[1],
                             (max_bbox[2] - min_bbox[2]) / base_res[2])

                offset = mathutils.Matrix()
                if not smoke_domain_mod:
                    offset = mathutils.Matrix.Translation((min_res[0]/base_res[0]*scale[0],
                    min_res[1]/base_res[1]*scale[1],
                    min_res[2]/base_res[2]*scale[2]))

                # Construct fluid matrix
                fluidmat[0][0] = nx / resolution[0]
                fluidmat[1][1] = ny / resolution[1]
                fluidmat[2][2] = nz / resolution[2]

                ob_scale = mathutils.Matrix()
                ob_scale[0][0] = resolution[0] / base_res[0]
                ob_scale[1][1] = resolution[1] / base_res[1]
                ob_scale[2][2] = resolution[2] / base_res[2]

                obmat = obmat @ ob_scale

                if self.use_bbox_offset:
                    obmat = offset @ obmat
                    
                fluidmat = fluidmat @ mathutils.Matrix.Translation(0.5 * mathutils.Vector(cell_size))
            else:
                fluidmat[0][0] = 1 / self.nx
                fluidmat[1][1] = 1 / self.ny
                fluidmat[2][2] = 1 / self.nz

                houdini_transform = mathutils.Matrix()
                if self.creator == "houdini":
                    # As y is Up in Houdini, switch y and z axis to fit coordonate frame of Blender
                    houdini_transform = mathutils.Matrix.Translation((0.5, 0.5, 0.5)) @ mathutils.Matrix.Rotation(
                        radians(90.0), 4, 'X') \
                                        @ mathutils.Matrix.Translation((-0.5, -0.5, -0.5))

                houdini_transform = houdini_transform @ ovdb
                obmat = mathutils.Matrix()
        # LuxCore normalize grid dimensions to [0..1] range, if the dimension of the bounding box of different grids
        # in one file is different the bounding box offset, e.g. lower corner of the box has to be considered,
        # e.g. in smoke / flame simulations

        if self.use_bbox_offset:
            fluidmat = fluidmat @ mathutils.Matrix.Translation(
                mathutils.Vector((bbox[0]/nx, bbox[1]/ny,bbox[2]/nz)))

        mapping_definitions = self.inputs["3D Mapping"].export(exporter, depsgraph, props)
        transformation = utils.list_to_matrix(mapping_definitions["mapping.transformation"])
        mapping_definitions["mapping.type"] = "globalmapping3d"
        # combine transformations
        mapping_definitions["mapping.transformation"] = utils.matrix_to_list(transformation @ obmat @ fluidmat @ houdini_transform,
                                                                             invert=True)

        definitions = {
            "type": "densitygrid",
            "wrap": "black",
            "storage": self.precision,
            "nx": nx,
            "ny": ny,
            "nz": nz,
            "openvdb.file": bpy.path.abspath(file_path),
            "openvdb.grid": grid_name,
        }
        definitions.update(mapping_definitions)

        return self.create_props(props, definitions, luxcore_name)

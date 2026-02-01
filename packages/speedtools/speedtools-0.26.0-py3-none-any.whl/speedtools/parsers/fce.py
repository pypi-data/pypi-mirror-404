# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild
# type: ignore

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 11):
    raise Exception("Incompatible Kaitai Struct Python API: 0.11 or later is required, but you have %s" % (kaitaistruct.__version__))

class Fce(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        super(Fce, self).__init__(_io)
        self._parent = _parent
        self._root = _root or self
        self._read()

    def _read(self):
        self.magic = self._io.read_bytes(4)
        if not self.magic == b"\x14\x10\x10\x00":
            raise kaitaistruct.ValidationNotEqualError(b"\x14\x10\x10\x00", self.magic, self._io, u"/seq/0")
        self.unknown = self._io.read_bytes(4)
        self.num_polygons = self._io.read_u4le()
        self.num_vertices = self._io.read_u4le()
        self.num_arts = self._io.read_u4le()
        self.vertice_table_offset = self._io.read_u4le()
        self.normals_table_offset = self._io.read_u4le()
        self.polygon_table_offset = self._io.read_u4le()
        self.unknown2 = self._io.read_bytes(12)
        self.undamaged_vertices_offset = self._io.read_u4le()
        self.undamaged_normals_offset = self._io.read_u4le()
        self.damaged_vertices_offset = self._io.read_u4le()
        self.damaged_normals_offset = self._io.read_u4le()
        self.damage_weights_offset = self._io.read_u4le()
        self.driver_movement_offset = self._io.read_u4le()
        self.unknown4 = self._io.read_bytes(8)
        self.half_sizes = Fce.Float3(self._io, self, self._root)
        self.num_light_sources = self._io.read_u4le()
        self.light_sources = []
        for i in range(self.num_light_sources):
            self.light_sources.append(Fce.Float3(self._io, self, self._root))

        self.unused_light_sources = []
        for i in range(16 - self.num_light_sources):
            self.unused_light_sources.append(Fce.Float3(self._io, self, self._root))

        self.num_car_parts = self._io.read_u4le()
        self.part_locations = []
        for i in range(self.num_car_parts):
            self.part_locations.append(Fce.Float3(self._io, self, self._root))

        self.unused_parts = []
        for i in range(64 - self.num_car_parts):
            self.unused_parts.append(Fce.Float3(self._io, self, self._root))

        self.part_vertex_index = []
        for i in range(self.num_car_parts):
            self.part_vertex_index.append(self._io.read_u4le())

        self.unused_part_vertex_index = []
        for i in range(64 - self.num_car_parts):
            self.unused_part_vertex_index.append(self._io.read_u4le())

        self.part_num_vertices = []
        for i in range(self.num_car_parts):
            self.part_num_vertices.append(self._io.read_u4le())

        self.unused_part_num_vertices = []
        for i in range(64 - self.num_car_parts):
            self.unused_part_num_vertices.append(self._io.read_u4le())

        self.part_polygon_index = []
        for i in range(self.num_car_parts):
            self.part_polygon_index.append(self._io.read_u4le())

        self.unused_part_polygon_index = []
        for i in range(64 - self.num_car_parts):
            self.unused_part_polygon_index.append(self._io.read_u4le())

        self.part_num_polygons = []
        for i in range(self.num_car_parts):
            self.part_num_polygons.append(self._io.read_u4le())

        self.unused_part_num_polygons = []
        for i in range(64 - self.num_car_parts):
            self.unused_part_num_polygons.append(self._io.read_u4le())

        self.num_colors = self._io.read_u4le()
        self.primary_colors = []
        for i in range(self.num_colors):
            self.primary_colors.append(Fce.Color(self._io, self, self._root))

        self.unused_primary_colors = []
        for i in range(16 - self.num_colors):
            self.unused_primary_colors.append(Fce.Color(self._io, self, self._root))

        self.interior_colors = []
        for i in range(self.num_colors):
            self.interior_colors.append(Fce.Color(self._io, self, self._root))

        self.unused_interior_colors = []
        for i in range(16 - self.num_colors):
            self.unused_interior_colors.append(Fce.Color(self._io, self, self._root))

        self.secondary_colors = []
        for i in range(self.num_colors):
            self.secondary_colors.append(Fce.Color(self._io, self, self._root))

        self.unused_secondary_colors = []
        for i in range(16 - self.num_colors):
            self.unused_secondary_colors.append(Fce.Color(self._io, self, self._root))

        self.driver_colors = []
        for i in range(self.num_colors):
            self.driver_colors.append(Fce.Color(self._io, self, self._root))

        self.unused_driver_colors = []
        for i in range(16 - self.num_colors):
            self.unused_driver_colors.append(Fce.Color(self._io, self, self._root))

        self.unknown5 = self._io.read_bytes(260)
        self._raw_dummies = []
        self.dummies = []
        for i in range(16):
            self._raw_dummies.append(self._io.read_bytes(64))
            _io__raw_dummies = KaitaiStream(BytesIO(self._raw_dummies[i]))
            self.dummies.append(Fce.Dummy(_io__raw_dummies, self, self._root))

        self._raw_part_strings = []
        self.part_strings = []
        for i in range(self.num_car_parts):
            self._raw_part_strings.append(self._io.read_bytes(64))
            _io__raw_part_strings = KaitaiStream(BytesIO(self._raw_part_strings[i]))
            self.part_strings.append(Fce.Part(_io__raw_part_strings, self, self._root))

        self._raw_unused_part_strings = []
        self.unused_part_strings = []
        for i in range(64 - self.num_car_parts):
            self._raw_unused_part_strings.append(self._io.read_bytes(64))
            _io__raw_unused_part_strings = KaitaiStream(BytesIO(self._raw_unused_part_strings[i]))
            self.unused_part_strings.append(Fce.Part(_io__raw_unused_part_strings, self, self._root))

        self.unknown8 = self._io.read_bytes(528)


    def _fetch_instances(self):
        pass
        self.half_sizes._fetch_instances()
        for i in range(len(self.light_sources)):
            pass
            self.light_sources[i]._fetch_instances()

        for i in range(len(self.unused_light_sources)):
            pass
            self.unused_light_sources[i]._fetch_instances()

        for i in range(len(self.part_locations)):
            pass
            self.part_locations[i]._fetch_instances()

        for i in range(len(self.unused_parts)):
            pass
            self.unused_parts[i]._fetch_instances()

        for i in range(len(self.part_vertex_index)):
            pass

        for i in range(len(self.unused_part_vertex_index)):
            pass

        for i in range(len(self.part_num_vertices)):
            pass

        for i in range(len(self.unused_part_num_vertices)):
            pass

        for i in range(len(self.part_polygon_index)):
            pass

        for i in range(len(self.unused_part_polygon_index)):
            pass

        for i in range(len(self.part_num_polygons)):
            pass

        for i in range(len(self.unused_part_num_polygons)):
            pass

        for i in range(len(self.primary_colors)):
            pass
            self.primary_colors[i]._fetch_instances()

        for i in range(len(self.unused_primary_colors)):
            pass
            self.unused_primary_colors[i]._fetch_instances()

        for i in range(len(self.interior_colors)):
            pass
            self.interior_colors[i]._fetch_instances()

        for i in range(len(self.unused_interior_colors)):
            pass
            self.unused_interior_colors[i]._fetch_instances()

        for i in range(len(self.secondary_colors)):
            pass
            self.secondary_colors[i]._fetch_instances()

        for i in range(len(self.unused_secondary_colors)):
            pass
            self.unused_secondary_colors[i]._fetch_instances()

        for i in range(len(self.driver_colors)):
            pass
            self.driver_colors[i]._fetch_instances()

        for i in range(len(self.unused_driver_colors)):
            pass
            self.unused_driver_colors[i]._fetch_instances()

        for i in range(len(self.dummies)):
            pass
            self.dummies[i]._fetch_instances()

        for i in range(len(self.part_strings)):
            pass
            self.part_strings[i]._fetch_instances()

        for i in range(len(self.unused_part_strings)):
            pass
            self.unused_part_strings[i]._fetch_instances()

        _ = self.damaged_normals
        if hasattr(self, '_m_damaged_normals'):
            pass
            for i in range(len(self._m_damaged_normals)):
                pass
                self._m_damaged_normals[i]._fetch_instances()


        _ = self.damaged_vertices
        if hasattr(self, '_m_damaged_vertices'):
            pass
            for i in range(len(self._m_damaged_vertices)):
                pass
                self._m_damaged_vertices[i]._fetch_instances()


        _ = self.movement_data
        if hasattr(self, '_m_movement_data'):
            pass
            for i in range(len(self._m_movement_data)):
                pass


        _ = self.normals
        if hasattr(self, '_m_normals'):
            pass
            for i in range(len(self._m_normals)):
                pass
                self._m_normals[i]._fetch_instances()


        _ = self.polygons
        if hasattr(self, '_m_polygons'):
            pass
            for i in range(len(self._m_polygons)):
                pass
                self._m_polygons[i]._fetch_instances()


        _ = self.undamaged_normals
        if hasattr(self, '_m_undamaged_normals'):
            pass
            for i in range(len(self._m_undamaged_normals)):
                pass
                self._m_undamaged_normals[i]._fetch_instances()


        _ = self.undamaged_vertices
        if hasattr(self, '_m_undamaged_vertices'):
            pass
            for i in range(len(self._m_undamaged_vertices)):
                pass
                self._m_undamaged_vertices[i]._fetch_instances()


        _ = self.vertex_damage_weights
        if hasattr(self, '_m_vertex_damage_weights'):
            pass
            for i in range(len(self._m_vertex_damage_weights)):
                pass


        _ = self.vertices
        if hasattr(self, '_m_vertices'):
            pass
            for i in range(len(self._m_vertices)):
                pass
                self._m_vertices[i]._fetch_instances()



    class Color(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fce.Color, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.hue = self._io.read_u1()
            self.saturation = self._io.read_u1()
            self.brightness = self._io.read_u1()
            self.unknown = self._io.read_bytes(1)


        def _fetch_instances(self):
            pass


    class Dummy(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fce.Dummy, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.magic = (self._io.read_bytes(1)).decode(u"ASCII")
            self.color = (self._io.read_bytes(1)).decode(u"ASCII")
            self.type = (self._io.read_bytes(1)).decode(u"ASCII")
            self.breakable = (self._io.read_bytes(1)).decode(u"ASCII")
            self.flashing = (self._io.read_bytes(1)).decode(u"ASCII")
            self.intensity = (self._io.read_bytes(1)).decode(u"ASCII")
            self.time_on = (self._io.read_bytes(1)).decode(u"ASCII")
            self.time_off = (self._io.read_bytes(1)).decode(u"ASCII")


        def _fetch_instances(self):
            pass


    class Float3(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fce.Float3, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.x = self._io.read_f4le()
            self.y = self._io.read_f4le()
            self.z = self._io.read_f4le()


        def _fetch_instances(self):
            pass


    class Part(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fce.Part, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.value = []
            i = 0
            while not self._io.is_eof():
                self.value.append((self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII"))
                i += 1



        def _fetch_instances(self):
            pass
            for i in range(len(self.value)):
                pass



    class Polygon(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fce.Polygon, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.texture = self._io.read_u4le()
            self.face = []
            for i in range(3):
                self.face.append(self._io.read_u4le())

            self.unknown = []
            for i in range(6):
                self.unknown.append(self._io.read_bytes(2))

            self.flags = self._io.read_u4le()
            self.u = []
            for i in range(3):
                self.u.append(self._io.read_f4le())

            self.v = []
            for i in range(3):
                self.v.append(self._io.read_f4le())



        def _fetch_instances(self):
            pass
            for i in range(len(self.face)):
                pass

            for i in range(len(self.unknown)):
                pass

            for i in range(len(self.u)):
                pass

            for i in range(len(self.v)):
                pass


        @property
        def backface_culling(self):
            if hasattr(self, '_m_backface_culling'):
                return self._m_backface_culling

            self._m_backface_culling = self.flags & 4 == 0
            return getattr(self, '_m_backface_culling', None)

        @property
        def highly_reflective(self):
            if hasattr(self, '_m_highly_reflective'):
                return self._m_highly_reflective

            self._m_highly_reflective = self.flags & 2 != 0
            return getattr(self, '_m_highly_reflective', None)

        @property
        def non_reflective(self):
            if hasattr(self, '_m_non_reflective'):
                return self._m_non_reflective

            self._m_non_reflective = self.flags & 1 != 0
            return getattr(self, '_m_non_reflective', None)

        @property
        def transparent(self):
            if hasattr(self, '_m_transparent'):
                return self._m_transparent

            self._m_transparent = self.flags & 8 != 0
            return getattr(self, '_m_transparent', None)


    @property
    def damaged_normals(self):
        """Damaged normal table."""
        if hasattr(self, '_m_damaged_normals'):
            return self._m_damaged_normals

        _pos = self._io.pos()
        self._io.seek(8248 + self.damaged_normals_offset)
        self._m_damaged_normals = []
        for i in range(self.num_vertices):
            self._m_damaged_normals.append(Fce.Float3(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_damaged_normals', None)

    @property
    def damaged_vertices(self):
        """Damaged vertice table."""
        if hasattr(self, '_m_damaged_vertices'):
            return self._m_damaged_vertices

        _pos = self._io.pos()
        self._io.seek(8248 + self.damaged_vertices_offset)
        self._m_damaged_vertices = []
        for i in range(self.num_vertices):
            self._m_damaged_vertices.append(Fce.Float3(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_damaged_vertices', None)

    @property
    def movement_data(self):
        """Vertex movement data."""
        if hasattr(self, '_m_movement_data'):
            return self._m_movement_data

        _pos = self._io.pos()
        self._io.seek(8248 + self.driver_movement_offset)
        self._m_movement_data = []
        for i in range(self.num_vertices):
            self._m_movement_data.append(self._io.read_u4le())

        self._io.seek(_pos)
        return getattr(self, '_m_movement_data', None)

    @property
    def normals(self):
        """Normal table."""
        if hasattr(self, '_m_normals'):
            return self._m_normals

        _pos = self._io.pos()
        self._io.seek(8248 + self.normals_table_offset)
        self._m_normals = []
        for i in range(self.num_vertices):
            self._m_normals.append(Fce.Float3(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_normals', None)

    @property
    def polygons(self):
        """Polygon table."""
        if hasattr(self, '_m_polygons'):
            return self._m_polygons

        _pos = self._io.pos()
        self._io.seek(8248 + self.polygon_table_offset)
        self._m_polygons = []
        for i in range(self.num_polygons):
            self._m_polygons.append(Fce.Polygon(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_polygons', None)

    @property
    def undamaged_normals(self):
        """Undamaged normal table."""
        if hasattr(self, '_m_undamaged_normals'):
            return self._m_undamaged_normals

        _pos = self._io.pos()
        self._io.seek(8248 + self.undamaged_normals_offset)
        self._m_undamaged_normals = []
        for i in range(self.num_vertices):
            self._m_undamaged_normals.append(Fce.Float3(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_undamaged_normals', None)

    @property
    def undamaged_vertices(self):
        """Undamaged vertice table."""
        if hasattr(self, '_m_undamaged_vertices'):
            return self._m_undamaged_vertices

        _pos = self._io.pos()
        self._io.seek(8248 + self.undamaged_vertices_offset)
        self._m_undamaged_vertices = []
        for i in range(self.num_vertices):
            self._m_undamaged_vertices.append(Fce.Float3(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_undamaged_vertices', None)

    @property
    def vertex_damage_weights(self):
        """Vertex damage weights."""
        if hasattr(self, '_m_vertex_damage_weights'):
            return self._m_vertex_damage_weights

        _pos = self._io.pos()
        self._io.seek(8248 + self.damage_weights_offset)
        self._m_vertex_damage_weights = []
        for i in range(self.num_vertices):
            self._m_vertex_damage_weights.append(self._io.read_f4le())

        self._io.seek(_pos)
        return getattr(self, '_m_vertex_damage_weights', None)

    @property
    def vertices(self):
        """Vertice table."""
        if hasattr(self, '_m_vertices'):
            return self._m_vertices

        _pos = self._io.pos()
        self._io.seek(8248 + self.vertice_table_offset)
        self._m_vertices = []
        for i in range(self.num_vertices):
            self._m_vertices.append(Fce.Float3(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_vertices', None)



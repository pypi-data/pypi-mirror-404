# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild
# type: ignore

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from enum import IntEnum


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 11):
    raise Exception("Incompatible Kaitai Struct Python API: 0.11 or later is required, but you have %s" % (kaitaistruct.__version__))

class Fsh(KaitaiStruct):

    class DataType(IntEnum):
        palette = 45
        text = 111
        bitmap16 = 120
        bitmap8 = 123
        bitmap32 = 125
        bitmap16_alpha = 126
    def __init__(self, _io, _parent=None, _root=None):
        super(Fsh, self).__init__(_io)
        self._parent = _parent
        self._root = _root or self
        self._read()

    def _read(self):
        self.magic = self._io.read_bytes(4)
        if not self.magic == b"\x53\x48\x50\x49":
            raise kaitaistruct.ValidationNotEqualError(b"\x53\x48\x50\x49", self.magic, self._io, u"/seq/0")
        self.length = self._io.read_u4le()
        self.num_resources = self._io.read_u4le()
        self.directory_id_string = self._io.read_bytes(4)
        if not self.directory_id_string == b"\x47\x49\x4D\x58":
            raise kaitaistruct.ValidationNotEqualError(b"\x47\x49\x4D\x58", self.directory_id_string, self._io, u"/seq/3")
        self.resources = []
        for i in range(self.num_resources):
            self.resources.append(Fsh.Resource(i, i == self.num_resources - 1, self._io, self, self._root))



    def _fetch_instances(self):
        pass
        for i in range(len(self.resources)):
            pass
            self.resources[i]._fetch_instances()


    class Bitmap(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fsh.Bitmap, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.unknown = self._io.read_u4le()
            self.x_pos = self._io.read_u2le()
            self.y_pos = self._io.read_u2le()
            self.data = []
            for i in range(self._parent.width * self._parent.height):
                _on = self._parent.code
                if _on == Fsh.DataType.bitmap16:
                    pass
                    self.data.append(Fsh.Pixel16Element(self._io, self, self._root))
                elif _on == Fsh.DataType.bitmap16_alpha:
                    pass
                    self.data.append(Fsh.Pixel16AlphaElement(self._io, self, self._root))
                elif _on == Fsh.DataType.bitmap32:
                    pass
                    self.data.append(Fsh.Pixel32Element(self._io, self, self._root))
                elif _on == Fsh.DataType.bitmap8:
                    pass
                    self.data.append(self._io.read_u1())
                elif _on == Fsh.DataType.palette:
                    pass
                    self.data.append(Fsh.Pixel16AlphaElement(self._io, self, self._root))



        def _fetch_instances(self):
            pass
            for i in range(len(self.data)):
                pass
                _on = self._parent.code
                if _on == Fsh.DataType.bitmap16:
                    pass
                    self.data[i]._fetch_instances()
                elif _on == Fsh.DataType.bitmap16_alpha:
                    pass
                    self.data[i]._fetch_instances()
                elif _on == Fsh.DataType.bitmap32:
                    pass
                    self.data[i]._fetch_instances()
                elif _on == Fsh.DataType.bitmap8:
                    pass
                elif _on == Fsh.DataType.palette:
                    pass
                    self.data[i]._fetch_instances()



    class DataBlock(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fsh.DataBlock, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.code = KaitaiStream.resolve_enum(Fsh.DataType, self._io.read_u1())
            self.extra_offset = self._io.read_bits_int_le(24)
            self.width = self._io.read_u2le()
            self.height = self._io.read_u2le()
            _on = self.code
            if _on == Fsh.DataType.text:
                pass
                self.data = (KaitaiStream.bytes_terminate(self._io.read_bytes((self._parent._io.size() - self._parent._io.pos() if self.is_last else self.extra_offset - 8)), 0, False)).decode(u"ASCII")
            else:
                pass
                self._raw_data = self._io.read_bytes((self._parent._io.size() - self._parent._io.pos() if self.is_last else self.extra_offset - 8))
                _io__raw_data = KaitaiStream(BytesIO(self._raw_data))
                self.data = Fsh.Bitmap(_io__raw_data, self, self._root)


        def _fetch_instances(self):
            pass
            _on = self.code
            if _on == Fsh.DataType.text:
                pass
            else:
                pass
                self.data._fetch_instances()

        @property
        def is_last(self):
            if hasattr(self, '_m_is_last'):
                return self._m_is_last

            self._m_is_last = self.extra_offset == 0
            return getattr(self, '_m_is_last', None)


    class Pixel16AlphaElement(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fsh.Pixel16AlphaElement, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.value = self._io.read_u2le()


        def _fetch_instances(self):
            pass

        @property
        def alpha(self):
            if hasattr(self, '_m_alpha'):
                return self._m_alpha

            self._m_alpha = (255 if self.value & 32768 != 0 else 0)
            return getattr(self, '_m_alpha', None)

        @property
        def blue(self):
            if hasattr(self, '_m_blue'):
                return self._m_blue

            self._m_blue = (self.value >> 10 & 31) * 8
            return getattr(self, '_m_blue', None)

        @property
        def color(self):
            """ARGB color value."""
            if hasattr(self, '_m_color'):
                return self._m_color

            self._m_color = ((self.blue + self.green * 256) + self.red * 65536) + self.alpha * 16777216
            return getattr(self, '_m_color', None)

        @property
        def green(self):
            if hasattr(self, '_m_green'):
                return self._m_green

            self._m_green = (self.value >> 5 & 31) * 8
            return getattr(self, '_m_green', None)

        @property
        def red(self):
            if hasattr(self, '_m_red'):
                return self._m_red

            self._m_red = (self.value & 31) * 8
            return getattr(self, '_m_red', None)


    class Pixel16Element(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fsh.Pixel16Element, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.value = self._io.read_u2le()


        def _fetch_instances(self):
            pass

        @property
        def alpha(self):
            if hasattr(self, '_m_alpha'):
                return self._m_alpha

            self._m_alpha = 255
            return getattr(self, '_m_alpha', None)

        @property
        def blue(self):
            if hasattr(self, '_m_blue'):
                return self._m_blue

            self._m_blue = (self.value >> 11 & 31) * 8
            return getattr(self, '_m_blue', None)

        @property
        def color(self):
            """ARGB color value."""
            if hasattr(self, '_m_color'):
                return self._m_color

            self._m_color = ((self.blue + self.green * 256) + self.red * 65536) + self.alpha * 16777216
            return getattr(self, '_m_color', None)

        @property
        def green(self):
            if hasattr(self, '_m_green'):
                return self._m_green

            self._m_green = (self.value >> 5 & 63) * 4
            return getattr(self, '_m_green', None)

        @property
        def red(self):
            if hasattr(self, '_m_red'):
                return self._m_red

            self._m_red = (self.value & 31) * 8
            return getattr(self, '_m_red', None)


    class Pixel32Element(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fsh.Pixel32Element, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.value = self._io.read_u4le()


        def _fetch_instances(self):
            pass

        @property
        def alpha(self):
            if hasattr(self, '_m_alpha'):
                return self._m_alpha

            self._m_alpha = self.value >> 24 & 255
            return getattr(self, '_m_alpha', None)

        @property
        def blue(self):
            if hasattr(self, '_m_blue'):
                return self._m_blue

            self._m_blue = self.value >> 16 & 255
            return getattr(self, '_m_blue', None)

        @property
        def color(self):
            """ARGB color value."""
            if hasattr(self, '_m_color'):
                return self._m_color

            self._m_color = ((self.blue + self.green * 256) + self.red * 65536) + self.alpha * 16777216
            return getattr(self, '_m_color', None)

        @property
        def green(self):
            if hasattr(self, '_m_green'):
                return self._m_green

            self._m_green = self.value >> 8 & 255
            return getattr(self, '_m_green', None)

        @property
        def red(self):
            if hasattr(self, '_m_red'):
                return self._m_red

            self._m_red = self.value & 255
            return getattr(self, '_m_red', None)


    class Resource(KaitaiStruct):
        def __init__(self, index, is_last, _io, _parent=None, _root=None):
            super(Fsh.Resource, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self.index = index
            self.is_last = is_last
            self._read()

        def _read(self):
            self.name = (self._io.read_bytes(4)).decode(u"ASCII")
            self.offset = self._io.read_u4le()


        def _fetch_instances(self):
            pass
            _ = self.body
            if hasattr(self, '_m_body'):
                pass
                self._m_body._fetch_instances()


        @property
        def body(self):
            if hasattr(self, '_m_body'):
                return self._m_body

            _pos = self._io.pos()
            self._io.seek(self.offset)
            self._raw__m_body = self._io.read_bytes(self.body_size)
            _io__raw__m_body = KaitaiStream(BytesIO(self._raw__m_body))
            self._m_body = Fsh.ResourceBody(_io__raw__m_body, self, self._root)
            self._io.seek(_pos)
            return getattr(self, '_m_body', None)

        @property
        def body_size(self):
            if hasattr(self, '_m_body_size'):
                return self._m_body_size

            self._m_body_size = (self._parent.resources[self.index + 1].offset - self.offset if (not (self.is_last)) else self._root._io.size() - self.offset)
            return getattr(self, '_m_body_size', None)


    class ResourceBody(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Fsh.ResourceBody, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.blocks = []
            i = 0
            while True:
                _ = Fsh.DataBlock(self._io, self, self._root)
                self.blocks.append(_)
                if _.extra_offset == 0:
                    break
                i += 1


        def _fetch_instances(self):
            pass
            for i in range(len(self.blocks)):
                pass
                self.blocks[i]._fetch_instances()





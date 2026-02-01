# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild
# type: ignore

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from speedtools.parsers import fce


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 11):
    raise Exception("Incompatible Kaitai Struct Python API: 0.11 or later is required, but you have %s" % (kaitaistruct.__version__))

class Viv(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        super(Viv, self).__init__(_io)
        self._parent = _parent
        self._root = _root or self
        self._read()

    def _read(self):
        self.magic = self._io.read_bytes(4)
        if not self.magic == b"\x42\x49\x47\x46":
            raise kaitaistruct.ValidationNotEqualError(b"\x42\x49\x47\x46", self.magic, self._io, u"/seq/0")
        self.size = self._io.read_u4be()
        self.num_entries = self._io.read_u4be()
        self.unknown = self._io.read_bytes(4)
        self.entries = []
        for i in range(self.num_entries):
            self.entries.append(Viv.DirectoryEntry(self._io, self, self._root))



    def _fetch_instances(self):
        pass
        for i in range(len(self.entries)):
            pass
            self.entries[i]._fetch_instances()


    class DirectoryEntry(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Viv.DirectoryEntry, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.offset = self._io.read_u4be()
            self.length = self._io.read_u4be()
            self.name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")


        def _fetch_instances(self):
            pass
            _ = self.body
            if hasattr(self, '_m_body'):
                pass
                _on = self.name
                if _on == u"car.fce":
                    pass
                    self._m_body._fetch_instances()
                elif _on == u"carp.txt":
                    pass
                elif _on == u"dash.fce":
                    pass
                    self._m_body._fetch_instances()
                elif _on == u"hel.fce":
                    pass
                    self._m_body._fetch_instances()
                else:
                    pass


        @property
        def body(self):
            if hasattr(self, '_m_body'):
                return self._m_body

            _pos = self._io.pos()
            self._io.seek(self.offset)
            _on = self.name
            if _on == u"car.fce":
                pass
                self._raw__m_body = self._io.read_bytes(self.length)
                _io__raw__m_body = KaitaiStream(BytesIO(self._raw__m_body))
                self._m_body = fce.Fce(_io__raw__m_body)
            elif _on == u"carp.txt":
                pass
                self._m_body = (KaitaiStream.bytes_terminate(self._io.read_bytes(self.length), 0, False)).decode(u"ASCII")
            elif _on == u"dash.fce":
                pass
                self._raw__m_body = self._io.read_bytes(self.length)
                _io__raw__m_body = KaitaiStream(BytesIO(self._raw__m_body))
                self._m_body = fce.Fce(_io__raw__m_body)
            elif _on == u"hel.fce":
                pass
                self._raw__m_body = self._io.read_bytes(self.length)
                _io__raw__m_body = KaitaiStream(BytesIO(self._raw__m_body))
                self._m_body = fce.Fce(_io__raw__m_body)
            else:
                pass
                self._m_body = self._io.read_bytes(self.length)
            self._io.seek(_pos)
            return getattr(self, '_m_body', None)




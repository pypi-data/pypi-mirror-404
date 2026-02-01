# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild
# type: ignore

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 11):
    raise Exception("Incompatible Kaitai Struct Python API: 0.11 or later is required, but you have %s" % (kaitaistruct.__version__))

class Sim(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        super(Sim, self).__init__(_io)
        self._parent = _parent
        self._root = _root or self
        self._read()

    def _read(self):
        self.heights = []
        i = 0
        while not self._io.is_eof():
            self.heights.append(self._io.read_f4le())
            i += 1



    def _fetch_instances(self):
        pass
        for i in range(len(self.heights)):
            pass




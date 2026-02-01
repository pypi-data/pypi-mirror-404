# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild
# type: ignore

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from speedtools.parsers import fsh
import speedtools


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 11):
    raise Exception("Incompatible Kaitai Struct Python API: 0.11 or later is required, but you have %s" % (kaitaistruct.__version__))

class Qfs(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        super(Qfs, self).__init__(_io)
        self._parent = _parent
        self._root = _root or self
        self._read()

    def _read(self):
        self.magic = self._io.read_bytes(2)
        if not self.magic == b"\x10\xFB":
            raise kaitaistruct.ValidationNotEqualError(b"\x10\xFB", self.magic, self._io, u"/seq/0")
        self.expanded_length = self._io.read_bits_int_be(24)
        self._raw__raw_data = self._io.read_bytes_full()
        _process = speedtools.Refpack(self.expanded_length)
        self._raw_data = _process.decode(self._raw__raw_data)
        _io__raw_data = KaitaiStream(BytesIO(self._raw_data))
        self.data = fsh.Fsh(_io__raw_data)


    def _fetch_instances(self):
        pass
        self.data._fetch_instances()



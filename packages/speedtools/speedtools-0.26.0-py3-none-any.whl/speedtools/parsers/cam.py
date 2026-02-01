# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild
# type: ignore

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 11):
    raise Exception("Incompatible Kaitai Struct Python API: 0.11 or later is required, but you have %s" % (kaitaistruct.__version__))

class Cam(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        super(Cam, self).__init__(_io)
        self._parent = _parent
        self._root = _root or self
        self._read()

    def _read(self):
        self.num_cameras = self._io.read_u4le()
        self.cameras = []
        for i in range(self.num_cameras):
            self.cameras.append(Cam.Camera(self._io, self, self._root))



    def _fetch_instances(self):
        pass
        for i in range(len(self.cameras)):
            pass
            self.cameras[i]._fetch_instances()


    class Camera(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Cam.Camera, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.type = self._io.read_u4le()
            self.location = Cam.Float3(self._io, self, self._root)
            self.transform = []
            for i in range(9):
                self.transform.append(self._io.read_f4le())

            self.unknown1 = self._io.read_f4le()
            self.start_road_block = self._io.read_u4le()
            self.unknown2 = self._io.read_bytes(4)
            self.end_road_block = self._io.read_u4le()


        def _fetch_instances(self):
            pass
            self.location._fetch_instances()
            for i in range(len(self.transform)):
                pass



    class Float3(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Cam.Float3, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.x = self._io.read_f4le()
            self.y = self._io.read_f4le()
            self.z = self._io.read_f4le()


        def _fetch_instances(self):
            pass




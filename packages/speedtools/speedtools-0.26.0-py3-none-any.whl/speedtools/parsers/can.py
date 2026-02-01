# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild
# type: ignore

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 11):
    raise Exception("Incompatible Kaitai Struct Python API: 0.11 or later is required, but you have %s" % (kaitaistruct.__version__))

class Can(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        super(Can, self).__init__(_io)
        self._parent = _parent
        self._root = _root or self
        self._read()

    def _read(self):
        self.head = self._io.read_u2le()
        self.type = self._io.read_u1()
        self.identifier = self._io.read_u1()
        self.num_keyframes = self._io.read_u2le()
        self.delay = self._io.read_u2le()
        self.keyframes = []
        for i in range(self.num_keyframes):
            self.keyframes.append(Can.Keyframe(self._io, self, self._root))



    def _fetch_instances(self):
        pass
        for i in range(len(self.keyframes)):
            pass
            self.keyframes[i]._fetch_instances()


    class Int3(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Can.Int3, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.ix = self._io.read_s4le()
            self.iy = self._io.read_s4le()
            self.iz = self._io.read_s4le()


        def _fetch_instances(self):
            pass

        @property
        def x(self):
            if hasattr(self, '_m_x'):
                return self._m_x

            self._m_x = (self.ix * 0.7692307692307693) / 65536
            return getattr(self, '_m_x', None)

        @property
        def y(self):
            if hasattr(self, '_m_y'):
                return self._m_y

            self._m_y = (self.iy * 0.7692307692307693) / 65536
            return getattr(self, '_m_y', None)

        @property
        def z(self):
            if hasattr(self, '_m_z'):
                return self._m_z

            self._m_z = (self.iz * 0.7692307692307693) / 65536
            return getattr(self, '_m_z', None)


    class Keyframe(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Can.Keyframe, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.location = Can.Int3(self._io, self, self._root)
            self.quaternion = Can.Short4(self._io, self, self._root)


        def _fetch_instances(self):
            pass
            self.location._fetch_instances()
            self.quaternion._fetch_instances()


    class Short4(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            super(Can.Short4, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.x = self._io.read_s2le()
            self.y = self._io.read_s2le()
            self.z = self._io.read_s2le()
            self.w = self._io.read_s2le()


        def _fetch_instances(self):
            pass




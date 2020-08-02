from nmigen_soc import csr

from .base import Register

class Word(Register):
    def __init__(self, address, *, reset=0x00000000):
        pass

class Bit(Register):
    def __init__(self, address, position, *, reset=False):
        self._address = address
        self._position = position

    def __get__(self, obj, type=None):
        key = (self._address, self._position)
        if not hasattr(obj, "_csr"):
            obj._csr = {}
        elif key in obj._csr:
            return obj._csr[key]

        elem = csr.Element(1, "rw", name=self._name)
        obj._csr[key] = elem
        return elem

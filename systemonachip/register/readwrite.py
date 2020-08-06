from nmigen import Record
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
        if not isinstance(obj._memory_window, Record):
            return (obj._memory_window[self._address + self._position // 8] & (1 << (self._position % 8))) != 0

        key = (self._address, self._position)
        if not hasattr(obj, "_csr"):
            obj._csr = {}
        elif key in obj._csr:
            return obj._csr[key]

        print("create bit", self._name)
        elem = csr.Element(1, "rw", name=self._name)
        obj._csr[key] = elem
        return elem


    def __set__(self, obj, type=None):
        if not isinstance(obj._memory_window, Record):
            obj._memory_window[self._address + self._position // 8] |= (1 << (self._position % 8))
            return

        raise RuntimeError("Cannot set value when elaborating")

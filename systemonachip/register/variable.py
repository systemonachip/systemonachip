"""Dynamically sized registers"""
from nmigen_soc import csr

class VariableWidth:
    def __init__(self, address, *, variable="_width"):
        """Variable width register that depends on instance state in the given `variable`. `variable`
           must start with `_` so it doesn't conflict with the register."""
        self._address = address
        self._width_variable = variable

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, type=None):
        if obj == None:
            return self
        key = (self._address, None)
        if not hasattr(obj, "_csr"):
            obj._csr = {}
        elif key in obj._csr:
            return obj._csr[key]

        elem = csr.Element(getattr(obj, self._width_variable), "rw", name=self._name)
        obj._csr[key] = elem
        return elem
from nmigen import Record, Signal

class Event:
    def __init__(self, address, bit, *, mode="rise"):
        self._address = address
        self._mode = mode
        self._bit = bit

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, type=None):
        if obj == None:
            return self

        if isinstance(obj._memory_window, Record):
            key = (self._bit, self._mode)
            if not hasattr(obj, "_events"):
                obj._events = {}
            elif key in obj._events:
                return obj._events[key]

            event  = Signal(name="{}_stb".format(self._name))
            obj._events[key] = event
            return event
        return (obj._memory_window[address] & (1 << self._bit)) != 0

class AggregateEvent:
    pass

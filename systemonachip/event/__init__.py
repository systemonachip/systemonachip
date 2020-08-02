from nmigen import Signal

class Event:
    def __init__(self, bit, *, mode="rise"):
        self._mode = mode
        self._bit = bit

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, type=None):
        if obj == None:
            return self
        key = (self._bit, self._mode)
        if not hasattr(obj, "_events"):
            obj._events = {}
        elif key in obj._events:
            return obj._events[key]

        event  = Signal(name="{}_stb".format(self._name))
        obj._events[key] = event
        print(obj._events)
        return event

class AggregateEvent:
    pass

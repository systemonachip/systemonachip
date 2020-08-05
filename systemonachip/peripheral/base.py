from nmigen import *
from nmigen import tracer
from nmigen.utils import log2_int

from nmigen_soc import csr, wishbone
from nmigen_soc.memory import MemoryMap
from nmigen_soc.csr.wishbone import WishboneCSRBridge

from ..register import AutoRegister
from ..event import *


__all__ = ["Peripheral"]


class Peripheral:
    """
    """
    def __init__(self, memory_window):
        self._memory_window = memory_window

    # def window(self, *, addr_width, data_width, granularity=None, features=frozenset(),
    #            alignment=0, addr=None, sparse=None):
    #     """Request a window to a subordinate bus.

    #     See :meth:`nmigen_soc.wishbone.Decoder.add` for details.

    #     Returns
    #     ------------
    #     An instance of :class:`nmigen_soc.wishbone.Interface`.
    #     """
    #     window = wishbone.Interface(addr_width=addr_width, data_width=data_width,
    #                                 granularity=granularity, features=features)
    #     granularity_bits = log2_int(data_width // window.granularity)
    #     window.memory_map = MemoryMap(addr_width=addr_width + granularity_bits,
    #                                   data_width=window.granularity, alignment=alignment)
    #     self._windows.append((window, addr, sparse))
    #     return window

    def elaborate(self, platform):
        m = Module()


        if hasattr(self, "_events"):
            print("events")
            for key in self._events:
                print(key, self._events[key])
            print()

        for name in dir(self):
            class_ = self.__class__
            if hasattr(class_, name):
                v = getattr(self.__class__, name)
                if isinstance(v, AutoRegister):
                    print(name, v)
                if isinstance(v, Event):
                    print("event", name, v)

        if hasattr(self, "_csr"):
            csr_mux = csr.Multiplexer(addr_width=1, data_width=8, alignment=1)

            print("csrs")
            for key in self._csr:
                addr, bit = key
                csr_mux.add(self._csr[key], addr=addr, alignment=1, extend=True)
                print(key, self._csr[key])
            print()

            m.submodules["csr_multiplexer"] = csr_mux
            # TODO: Only create this bridge if we were passed in a wishbone bus.
            m.submodules["wishbone_to_csr_bridge"] = WishboneCSRBridge(csr_mux.bus, data_width=8)

        return m


class PeripheralBridge(Elaboratable):
    """Peripheral bridge.

    A bridge providing access to the registers and windows of a peripheral, and support for
    interrupt requests from its event sources.

    Event managment is performed by an :class:`InterruptSource` submodule.

    Parameters
    ----------
    periph : :class:`Peripheral`
        The peripheral whose resources are exposed by this bridge.
    data_width : int
        Data width. See :class:`nmigen_soc.wishbone.Interface`.
    granularity : int or None
        Granularity. See :class:`nmigen_soc.wishbone.Interface`.
    features : iter(str)
        Optional signal set. See :class:`nmigen_soc.wishbone.Interface`.
    alignment : int
        Resource alignment. See :class:`nmigen_soc.memory.MemoryMap`.

    Attributes
    ----------
    bus : :class:`nmigen_soc.wishbone.Interface`
        Wishbone bus providing access to the resources of the peripheral.
    irq : :class:`IRQLine`, out
        Interrupt request. It is raised if any event source is enabled and has a pending
        notification.
    """
    def __init__(self, periph, *, data_width, granularity, features, alignment):
        if not isinstance(periph, Peripheral):
            raise TypeError("Peripheral must be an instance of Peripheral, not {!r}"
                            .format(periph))

        self._wb_decoder = wishbone.Decoder(addr_width=1, data_width=data_width,
                                            granularity=granularity,
                                            features=features, alignment=alignment)

        self._csr_subs = []

        for bank, bank_addr, bank_alignment in periph.iter_csr_banks():
            if bank_alignment is None:
                bank_alignment = alignment
            csr_mux = csr.Multiplexer(addr_width=1, data_width=8, alignment=bank_alignment)
            for elem, elem_addr, elem_alignment in bank.iter_csr_regs():
                if elem_alignment is None:
                    elem_alignment = alignment
                csr_mux.add(elem, addr=elem_addr, alignment=elem_alignment, extend=True)

            csr_bridge = WishboneCSRBridge(csr_mux.bus, data_width=data_width)
            self._wb_decoder.add(csr_bridge.wb_bus, addr=bank_addr, extend=True)
            self._csr_subs.append((csr_mux, csr_bridge))

        for window, window_addr, window_sparse in periph.iter_windows():
            self._wb_decoder.add(window, addr=window_addr, sparse=window_sparse, extend=True)

        events = list(periph.iter_events())
        if len(events) > 0:
            self._int_src = InterruptSource(events, name="{}_ev".format(periph.name))
            self.irq      = self._int_src.irq

            csr_mux = csr.Multiplexer(addr_width=1, data_width=8, alignment=alignment)
            csr_mux.add(self._int_src.status,  extend=True)
            csr_mux.add(self._int_src.pending, extend=True)
            csr_mux.add(self._int_src.enable,  extend=True)

            csr_bridge = WishboneCSRBridge(csr_mux.bus, data_width=data_width)
            self._wb_decoder.add(csr_bridge.wb_bus, extend=True)
            self._csr_subs.append((csr_mux, csr_bridge))
        else:
            self._int_src = None
            self.irq      = None

        self.bus = self._wb_decoder.bus

    def elaborate(self, platform):
        m = Module()

        for i, (csr_mux, csr_bridge) in enumerate(self._csr_subs):
            m.submodules[   "csr_mux_{}".format(i)] = csr_mux
            m.submodules["csr_bridge_{}".format(i)] = csr_bridge

        if self._int_src is not None:
            m.submodules._int_src = self._int_src

        m.submodules.wb_decoder = self._wb_decoder

        return m

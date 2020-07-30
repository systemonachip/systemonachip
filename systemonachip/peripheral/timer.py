from nmigen import *

from . import Peripheral


__all__ = ["Timer"]


class Timer(Peripheral, Elaboratable):
    """Timer peripheral.

    A general purpose down-counting timer peripheral."""

    creator_id = StaticHalfWord(0x0, 0x1248)
    """Creator id for Scott Shawcroft: 0x1248"""

    creation_id = StaticHalfWord(0x2, 0x0000)
    """Creation id: 0x0000"""

    reload_ = Word(0x4)
    """Reload value of counter. When `ctr` reaches 0, it is automatically reloaded with this value.
       If the written value is larger than the timer width, only the bits within the timer's range
       will be kept."""
    
    enable = Bit(0x8, 0x0)
    """Counter enable."""
    
    value = Word(0xb)
    """Counter value."""

    zero = Event(mode="rise")
    """Counter value reached 0."""

    def __init__(self, memory_window, width):
        """Parameters
        ----------
        width : int
            Counter width.

        Attributes
        ----------
        bus : :class:`nmigen_soc.wishbone.Interface`
            Wishbone bus interface.
        irq : :class:`IRQLine`
            Interrupt request.
        """
        super().__init__()

        if not isinstance(width, int) or width < 0:
            raise ValueError("Counter width must be a non-negative integer, not {!r}"
                             .format(width))
        if width > 32:
            raise ValueError("Counter width cannot be greater than 32 (was: {})"
                             .format(width))
        self.width   = width

        # bank          = self.csr_bank()
        # self._reload  = bank.csr(width, "rw")
        # self._en      = bank.csr(    1, "rw")
        # self._ctr     = bank.csr(width, "rw")

        # self._zero_ev = self.event(mode="rise")

        self._bridge  = self.bridge(data_width=32, granularity=8, alignment=2)
        self.bus      = self._bridge.bus
        self.irq      = self._bridge.irq

    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge = self._bridge

        with m.If(self.enable.r_data):
            with m.If(self.counter.r_data == 0):
                m.d.comb += self.zero.stb.eq(1)
                m.d.sync += self.value.r_data.eq(self.reload_.r_data)
            with m.Else():
                m.d.sync += self.value.r_data.eq(self.value.r_data - 1)

        with m.If(self.reload_.w_stb):
            m.d.sync += self.reload_.r_data.eq(self.reload_.w_data)
        with m.If(self._en.w_stb):
            m.d.sync += self.enable.r_data.eq(self.enable.w_data)
        with m.If(self.value.w_stb):
            m.d.sync += self.value.r_data.eq(self.value.w_data)

        return m

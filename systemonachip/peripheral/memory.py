from nmigen import *
from nmigen.utils import log2_int

from nmigen_soc import wishbone
from nmigen_soc.memory import MemoryMap

from nmigen import tracer

__all__ = ["RandomAccessMemory"]


class RandomAccessMemory(Elaboratable):
    """SRAM storage peripheral.

    Parameters
    ----------
    size : int
        Memory size in bytes.
    data_width : int
        Bus data width.
    granularity : int
        Bus granularity.
    writable : bool
        Memory is writable.

    Attributes
    ----------
    bus : :class:`nmigen_soc.wishbone.Interface`
        Wishbone bus interface.
    """
    # TODO raise bus.err if read-only and a bus write is attempted.
    def __init__(self, memory_window, *, size, name=None, src_loc_at=1, data_width=32, granularity=8, writable=True):
        super().__init__()
        if name is not None and not isinstance(name, str):
            raise TypeError("Name must be a string, not {!r}".format(name))
        self.name = name or tracer.get_var_name(depth=2 + src_loc_at).lstrip("_")

        if not isinstance(size, int) or size <= 0 or size & size-1:
            raise ValueError("Size must be an integer power of two, not {!r}"
                             .format(size))
        if size < data_width // granularity:
            raise ValueError("Size {} cannot be lesser than the data width/granularity ratio "
                             "of {} ({} / {})"
                              .format(size, data_width // granularity, data_width, granularity))

        self._mem  = Memory(depth=(size * granularity) // data_width, width=data_width,
                            name=self.name)

        if isinstance(memory_window, wishbone.Interface):
            if not hasattr(memory_window, "bte"):
                raise ValueError("Incoming wishbone.Interface must support burst")
            self.bus = memory_window
            self.bus.memory_map.add_resource(self._mem, size=size)

        self.size        = size
        self.granularity = granularity
        self.writable    = writable

    @property
    def init(self):
        return self._mem.init

    @init.setter
    def init(self, init):
        self._mem.init = init

    def elaborate(self, platform):
        m = Module()

        incr = Signal.like(self.bus.adr)

        with m.Switch(self.bus.bte):
            with m.Case(wishbone.BurstTypeExt.LINEAR):
                m.d.comb += incr.eq(self.bus.adr + 1)
            with m.Case(wishbone.BurstTypeExt.WRAP_4):
                m.d.comb += incr[:2].eq(self.bus.adr[:2] + 1)
                m.d.comb += incr[2:].eq(self.bus.adr[2:])
            with m.Case(wishbone.BurstTypeExt.WRAP_8):
                m.d.comb += incr[:3].eq(self.bus.adr[:3] + 1)
                m.d.comb += incr[3:].eq(self.bus.adr[3:])
            with m.Case(wishbone.BurstTypeExt.WRAP_16):
                m.d.comb += incr[:4].eq(self.bus.adr[:4] + 1)
                m.d.comb += incr[4:].eq(self.bus.adr[4:])

        m.submodules.mem_rp = mem_rp = self._mem.read_port()
        m.d.comb += self.bus.dat_r.eq(mem_rp.data)

        with m.If(self.bus.ack):
            m.d.sync += self.bus.ack.eq(0)

        with m.If(self.bus.cyc & self.bus.stb):
            m.d.sync += self.bus.ack.eq(1)
            with m.If((self.bus.cti == wishbone.CycleType.INCR_BURST) & self.bus.ack):
                m.d.comb += mem_rp.addr.eq(incr)
            with m.Else():
                m.d.comb += mem_rp.addr.eq(self.bus.adr)

        if self.writable:
            m.submodules.mem_wp = mem_wp = self._mem.write_port(granularity=self.granularity)
            m.d.comb += mem_wp.addr.eq(mem_rp.addr)
            m.d.comb += mem_wp.data.eq(self.bus.dat_w)
            with m.If(self.bus.cyc & self.bus.stb & self.bus.we):
                m.d.comb += mem_wp.en.eq(self.bus.sel)

        return m

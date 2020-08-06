from nmigen import *

from . import Peripheral

from ..event import *
from ..register import *


__all__ = ["Timer"]


class Timer(Peripheral, Elaboratable):
    """Timer peripheral.

    A general purpose down-counting timer peripheral."""

    creator_id = StaticHalfWord(0x0, 0x1248)
    """Creator id for Scott Shawcroft: 0x1248"""

    creation_id = StaticHalfWord(0x2, 0x0000)
    """Creation id: 0x0000"""

    reload_ = VariableWidth(0x4)
    """Reload value of counter. When `ctr` reaches 0, it is automatically reloaded with this value.
       If the written value is larger than the timer width, only the bits within the timer's range
       will be kept."""
    
    enable = Bit(0x8, 0x0)
    """Counter enable."""
    
    value = VariableWidth(0xc)
    """Counter value."""

    event_enable = AggregateEventEnable(0x10)
    """Enables interrupt generation out of the peripheral."""

    event_status = AggregateEventStatus(0x14)
    """Aggregate event status, write 0 to any bit to turn the interrupt off."""

    width = Config(0x18, "_width")
    """Configured width of the timer. Read-only"""

    zero = Event(0x14, 0x0, mode="rise")
    """Counter value reached 0. Event bit 0."""

    aggregate_event = AggregateEvent()
    """High signal when any individual event is active and enabled."""

    def __init__(self, memory_window, *, width=None):
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
        super().__init__(memory_window)

        if isinstance(memory_window, Record):
            if not isinstance(width, int) or width < 0:
                raise ValueError("Counter width must be a non-negative integer, not {!r}"
                                 .format(width))
            if width > 32:
                raise ValueError("Counter width cannot be greater than 32 (was: {})"
                                 .format(width))
            self._width   = width

        # bank          = self.csr_bank()
        # self._reload  = bank.csr(width, "rw")
        # self._en      = bank.csr(    1, "rw")
        # self._ctr     = bank.csr(width, "rw")

        # self._zero_ev = self.event(mode="rise")

        # self._bridge  = self.bridge(data_width=32, granularity=8, alignment=2)
        # self.bus      = self._bridge.bus
        #self.irq      = self._bridge.irq

    def elaborate(self, platform):
        m = Module()

        with m.If(self.enable.r_data):
            with m.If(self.value.r_data == 0):
                m.d.comb += self.zero.eq(1)
                m.d.sync += self.value.r_data.eq(self.reload_.r_data)
            with m.Else():
                m.d.sync += self.value.r_data.eq(self.value.r_data - 1)

        with m.If(self.reload_.w_stb):
            m.d.sync += self.reload_.r_data.eq(self.reload_.w_data)
        with m.If(self.enable.w_stb):
            m.d.sync += self.enable.r_data.eq(self.enable.w_data)
        with m.If(self.value.w_stb):
            m.d.sync += self.value.r_data.eq(self.value.w_data)

        m.submodules.peripheral = super().elaborate(platform)
        return m

if __name__ == "__main__":
    from nmigen.back.pysim import Simulator
    from nmigen.back import verilog
    bus = csr.Interface(addr_width=14,
                        data_width=8,
                        name="csr")
    t = Timer(bus, width=4)

    class SimulatorBus:
        def __init__(self, sim, bus):
            self._sim = sim
            self._bus = bus
            self._read_address = None
            self._read_data = None
            self._write_address = None
            self._write_data = None

        def actions(self):
            while True:
                if self._read_address is not None:
                    yield self._bus.addr.eq(self._read_address)
                    yield self._bus.r_stb.eq(1)
                    yield
                    yield self._bus.r_stb.eq(0)
                    x = yield self._bus.r_data
                    print(x)
                    yield
                    #print(yield self._bus.r_data)
                    # x = yield self._bus.r_data
                    # print("data read", x)
                    # yield

                    # x = yield self._bus.r_data
                    # print(x)
                    self._read_data = x
                    self._read_address = None
                elif self._write_address is not None and self._write_data is not None:
                    yield bus.addr.eq(self._write_address)
                    yield bus.w_data.eq(self._write_data)
                    yield bus.w_stb.eq(1)
                    yield
                    yield bus.w_stb.eq(0)
                    yield
                    yield
                    self._write_address = None
                    self._write_data = None
                else:
                    yield

        def __getitem__(self, index):
            #print("get", index, sim, bus)
            self._read_address = index
            while self._read_data is None:
                self._sim.advance()
            data = self._read_data
            print("got data", data)
            self._read_data = None
            return data

        def __setitem__(self, index, value):
            print("set", index, sim, bus)
            self._write_address = index
            self._write_data = value
            while self._write_data is not None:
                self._sim.advance()

    sim = Simulator(t)
    sbus = SimulatorBus(sim, bus)
    sim.add_clock(1e-6)
    sim.add_sync_process(sbus.actions)

    timer0 = Timer(sbus)
    with sim.write_vcd("timer.vcd"):
        print(timer0.width) # Should be 2
        timer0.reload_ = 0xf
        timer0.value = 0xe
        print(timer0.enable) # Should be False
        timer0.enable = True
        for _ in range(50):
            sim.advance()
        print(timer0.enable)
        print(timer0.value)
        # wait 5 cycles
        print(timer0.zero)
        print(timer0.value)

    with open("timer.v", "w") as f:
        f.write(verilog.convert(t))

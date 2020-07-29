import argparse
import importlib

from nmigen import *
from nmigen_soc import wishbone

from systemonachip.cpu.minerva import MinervaCPU
from systemonachip.peripheral.interrupt import GenericInterruptController
from systemonachip.peripheral.serial import AsyncSerial
from systemonachip.peripheral.memory import RandomAccessMemory
from systemonachip.peripheral.timer import Timer
from systemonachip.soc.cpu import CPUSoC


__all__ = ["Basic"]


class Basic(CPUSoC, Elaboratable):
    def __init__(self, *, clock_frequency, rom_size, ram_size):
        self._arbiter = wishbone.Arbiter(addr_width=30, data_width=32, granularity=8,
                                         features={"cti", "bte"})
        self._decoder = wishbone.Decoder(addr_width=30, data_width=32, granularity=8,
                                         features={"cti", "bte"})

        self.cpu = MinervaCPU(reset_address=0x00000000)
        self._arbiter.add(self.cpu.ibus)
        self._arbiter.add(self.cpu.dbus)

        self.rom = RandomAccessMemory(size=rom_size, writable=False)
        self._decoder.add(self.rom.bus, addr=0x00000000)

        self.ram = RandomAccessMemory(size=ram_size)
        self._decoder.add(self.ram.bus, addr=0x20000000)

        # self.uart = AsyncSerial(divisor=uart_divisor, pins=uart_pins)
        # self._decoder.add(self.uart.bus, addr=uart_addr)

        self.timer = Timer(width=32)
        self._decoder.add(self.timer.bus, addr=0x40000000)

        self.intc = GenericInterruptController(width=len(self.cpu.ip))
        self.intc.add_irq(self.timer.irq, 0)
        # self.intc.add_irq(self.uart .irq, 1)

        self.memory_map = self._decoder.bus.memory_map

        self.clk_freq = clock_frequency

    def elaborate(self, platform):
        m = Module()

        for name in dir(self):
            attr = getattr(self, name)
            if isinstance(attr, Elaboratable):
                setattr(m.submodules, name, attr)

        m.d.comb += [
            self._arbiter.bus.connect(self._decoder.bus),
            self.cpu.ip.eq(self.intc.ip),
        ]

        return m


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("platform", type=str,
            help="target platform (e.g. 'nmigen_boards.arty_a7.ArtyA7Platform')")
    parser.add_argument("--baudrate", type=int,
            default=9600,
            help="UART baudrate (default: 9600)")

    args = parser.parse_args()

    def get_platform(platform_name):
        module_name, class_name = platform_name.rsplit(".", 1)
        module = importlib.import_module(name=module_name)
        platform_class = getattr(module, class_name)
        return platform_class()

    platform = get_platform(args.platform)

    uart_divisor = int(platform.default_clk_frequency // args.baudrate)
    #uart_pins = platform.request("uart", 0)

    soc = Basic(clock_frequency=int(platform.default_clk_frequency), rom_size=0x4000,ram_size=0x1000)

    soc.build(do_build=True, do_init=True)
    platform.build(soc, do_program=True)

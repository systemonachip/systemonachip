# Another framework for building SoCs with nMigen

`systemonachip` is a set of Python primitives helpful when connecting system-on-a-chip components in an FPGA. It is based on [lambdasoc](https://github.com/lambdaconcept/lambdasoc), [nmigen-soc][nmigen-soc] and [nmigen](https://github.com/nmigen/nmigen/).

It does three things differently to make it easier for hardware beginners and possible to reuse as drivers:

1. This library uses full names for things rather than acronyms so that it's possible to understand what something is. Acronyms may be used after the full name has been used.
2. Peripherals take input busses and signals as constructor arguments to make it possible to switch from hardware generation to using the class as a driver.
3. Data descriptors are used to define registers. This makes them easy to document and the underlying code easy to reuse.

## Installation

```
git clone https://github.com/tannewt/systemonachip
cd lambdasoc
git submodule update --init --recursive

pip install -r requirements.txt
python setup.py install
```

## Quick start

Let's build and run the SoC example at [examples/sram_soc.py][sram_soc]. It is composed of a [Minerva][minerva] CPU, SRAM storage, an UART and a timer.

## License

LambdaSoC is released under the permissive two-clause BSD license. See LICENSE file for full copyright and license information.

[nmigen-soc]: https://github.com/nmigen/nmigen-soc
[minerva]: https://github.com/lambdaconcept/minerva
[nmigen-boards]: https://github.com/nmigen/nmigen-boards
[sram_soc]: https://github.com/lambdaconcept/lambdasoc/blob/master/examples/sram_soc.py

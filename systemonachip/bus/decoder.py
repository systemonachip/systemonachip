import math

from nmigen_soc import wishbone

class DecoderWindow:
	def __init__(self, decoder, address):
		self._decoder = decoder
		self._address = address

	def add(self, sub_bus):
		self._decoder.add(sub_bus, addr=self._address)

class Decoder(wishbone.Decoder):
	"""A decoder splits the incoming address space into evenly spaced chunks of
	   the given window_size. Each chunk is accessible by index."""
	def __init__(self, window_size, memory_window=None):
		super().__init__(addr_width=30, data_width=32)
		self.memory_window_bits = 32
		self.start_address = 0
		self.bin_size = window_size
		if memory_window:
			pass
		bits = int(math.log2(window_size))
		self._bins = [None] * (2 ** (self.memory_window_bits - bits))

	def __getitem__(self, index):
		if index > len(self._bins):
			raise IndexError("Invalid bin")
		if self._bins[index]:
			return self._bins[index]
		window = DecoderWindow(self, self.start_address + index * self.bin_size)
		self._bins[index] = window
		return window

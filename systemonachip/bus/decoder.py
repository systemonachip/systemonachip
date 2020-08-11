import math

from nmigen_soc import wishbone

from nmigen_soc import memory

class DecoderWindow:
	def __init__(self, parent_window, address, bin_size):
		self._parent = parent_window
		self._address = address
		self._bin_size = bin_size

	def __getitem__(self, index):
		if index > bin_size or index < -bin_size:
			raise IndexError()
		if index < 0:
			index += bin_size
		return self._parent[self._address + index]

	def __setitem__(self, index, value):
		if index > bin_size or index < -bin_size:
			raise IndexError()
		if index < 0:
			index += bin_size
		self._parent[self._address + index] = value


class Decoder(wishbone.Decoder):
	"""A decoder splits the incoming address space into evenly spaced chunks of
	   the given window_size. Each chunk is accessible by index."""
	def __init__(self, memory_window, window_size, *, cycle_type=True, burst_type=True):
		self.features = []
		if cycle_type:
			self.features.append("cti")
		if burst_type:
			self.features.append("bte")
		super().__init__(addr_width=memory_window.addr_width, data_width=memory_window.data_width, features=self.features)
		self.memory_window_bits = 32
		self.start_address = 0
		self.bin_size = window_size
		self._sub_bus_address_bits = int(math.log2(window_size))
		self._bins = [None] * (2 ** (self.memory_window_bits - self._sub_bus_address_bits))
		self._memory_window = memory_window

	def __getitem__(self, index):
		if index > len(self._bins):
			raise IndexError("Invalid bin")
		if self._bins[index]:
			return self._bins[index]
		bin_address = self.start_address + index * self.bin_size
		if isinstance(self._memory_window, wishbone.Interface):
			window = wishbone.Interface(addr_width=self._sub_bus_address_bits, data_width=self._memory_window.data_width, features=self.features)
			window.memory_map = memory.MemoryMap(addr_width=self._sub_bus_address_bits, data_width=self._memory_window.data_width)
			self.add(window, addr=bin_address, extend=True)
		else:
			window = DecoderWindow(self._memory_window, bin_address, self.bin_size)
		self._bins[index] = window
		return window

"""Dynamically sized registers"""

class VariableWidth:
	def __init__(self, address, *, variable="_width"):
		"""Variable width register that depends on instance state in the given `variable`. `variable`
	       must start with `_` so it doesn't conflict with the register."""
		pass

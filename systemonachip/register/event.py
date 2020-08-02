"""Event related registers"""

from .base import AutoRegister

class AggregateEventEnable(AutoRegister):
	def __init__(self, address):
		pass

class AggregateEventStatus(AutoRegister):
	def __init__(self, address):
		pass

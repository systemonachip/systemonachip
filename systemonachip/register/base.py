class Register:
    """Core register used for configuration and status info. 32bit registers may take multiple bus
       cycles to read to save footprint.

       By default, registers must be read during elaboration to exist."""
    
    def __set_name__(self, owner, name):
        self._name = name


class AutoRegister(Register):
    """Register that will be auto-created and doesn't need to be read during elaboration."""
    pass

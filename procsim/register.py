from functools import total_ordering

@total_ordering
class Register:
    """A Register capable of storing a single value.

    Args:
        value: Initial Register value.
    """

    def __init__(self, value=None):
        self.value = value

    def __lt__(self, other):
        """Return True if less than the immediate or Register value."""
        if isinstance(other, Register):
            return self.value < other.value
        return self.value < other

    def __eq__(self, other):
        """Return True if equal to the immediate or Register value."""
        if isinstance(other, Register):
            return self.value == other.value
        return self.value == other

    def __add__(self, other):
        """Add an immediate or Register value to the current Register's value."""
        if isinstance(other, Register):
            return Register(self.value + other.value)
        return Register(self.value + other)

    def __sub__(self, other):
        """Add an immediate or Register value to the current Register's value."""
        if isinstance(other, Register):
            return Register(self.value - other.value)
        return Register(self.value - other)

    def __repr__(self):
        return 'Register(%s)' % self.value

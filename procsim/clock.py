from procsim.tickable import Tickable

class Clock:
    """Simple processor clock to coordinate component execution."""

    def __init__(self):
        self.tickables = []

    def register(self, tickable):
        """Register a Tickable with the Clock."""
        assert_msg = 'Non-Tickable object attempted to register with Clock'
        assert isinstance(tickable, Tickable), assert_msg
        self.tickables.append(tickable)

    def tick(self):
        """Call tick on every Tickable.

        Call order is arbitrary - the components must not have tick
        dependencies. This can be achieved by implementing the Tickable
        interface.
        """
        for tickable in self.tickables:
            tickable.tick()

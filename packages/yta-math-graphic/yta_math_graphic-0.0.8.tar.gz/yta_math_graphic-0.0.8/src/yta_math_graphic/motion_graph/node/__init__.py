from dataclasses import dataclass


@dataclass
class MotionNode:
    """
    A node within a `MotionGraph` to represent a
    position and the time that takes to reach
    that position.
    """

    @property
    def position(
        self
    ) -> tuple[int, int]:
        """
        Get the position as a tuple `(self.x, self.y)`.
        """
        return (self.x, self.y)

    def __init__(
        self,
        x: float,
        y: float,
        duration: float
    ):
        self.x: float = x
        """
        The `x` position of the node.
        """
        self.y: float = y
        """
        The `y` position of the node.
        """
        self.duration: float = duration
        """
        The amount of time (in seconds) that takes to
        travel the distance in `x` from the previous
        node to this one.
        """
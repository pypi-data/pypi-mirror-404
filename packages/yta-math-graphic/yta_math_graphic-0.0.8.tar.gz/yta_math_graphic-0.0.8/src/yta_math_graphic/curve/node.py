from yta_validation.parameter import ParameterValidator
from dataclasses import dataclass


@dataclass
class CurveNode:
    """
    A node within a curve.
    """

    def __init__(
        self,
        x: float,
        y: float
    ):
        ParameterValidator.validate_mandatory_float('x', x)
        ParameterValidator.validate_mandatory_float('y', y)

        self.x: float = x
        """
        The `x` position of the node.
        """
        self.y: float = y
        """
        The `y` position of the node.
        """
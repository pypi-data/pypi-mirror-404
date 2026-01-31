from yta_math_graphic.curve.node import CurveNode
from typing import Union


"""
TODO: As we always want the nodes in order
for this general Curve concept, we could
force them to be ordered before storing them
when the `add_node` is called, so the `x_min`
and those properties are easier.
"""
class CurveDefinition:
    """
    The definition of a curve.
    """

    @property
    def nodes(
        self
    ) -> list[CurveNode]:
        """
        The list of nodes but ordered by the `x` value.

        This value is cached.
        """
        if self._nodes_ordered is None:
            self._nodes_ordered = tuple(sorted(self._nodes, key = lambda node: node.x))

        return self._nodes_ordered
    
    @property
    def x_min(
        self
    ) -> Union[float, None]:
        """
        The minimum `x` value, as a normalized value in
        the `[0.0, 1.0]` range. Useful value to use for
        the axis and because it is where the progress
        starts.
        """
        return min(
            (
                node.x
                for node in self.nodes
            ),
            default = None
        )
    
    @property
    def x_max(
        self
    ) -> Union[float, None]:
        """
        The maximum `x` value, as a normalized value in
        the `[0.0, 1.0]` range. Useful value to use for
        the axis and because it is where the progress
        ends.
        """
        return max(
            (
                node.x
                for node in self.nodes
            ),
            default = None
        )
    
    @property
    def y_min(
        self
    ) -> Union[float, None]:
        """
        The minimum `y` value, as a normalized value in
        the `[0.0, 1.0]` range.
        """
        return min(
            (
                node.y
                for node in self.nodes
            ),
            default = None
        )
    
    @property
    def y_max(
        self
    ) -> Union[float, None]:
        """
        The maximum `y` value, as a normalized value in
        the `[0.0, 1.0]` range.
        """
        return max(
            (
                node.y
                for node in self.nodes
            ),
            default = None
        )
    
    @property
    def distance(
        self
    ) -> Union[float, None]:
        """
        The total length (as a normalized value) of the
        segments we have in this definition.

        The formula:
        ```
        self.x_max - self.x_min
        ```
        """
        return (
            self.x_max - self.x_min
            if self.x_max is not None else
            None
        )
    
    @property
    def number_of_segments(
        self
    ) -> int:
        """
        The number of segments that the curve has according
        to the amount of nodes included.
        """
        return max(0, len(self._nodes) - 1)
    
    def __init__(
        self,
        x_value_range: tuple[float, float] = (0.0, 1.0),
        y_value_range: tuple[float, float] = (0.0, 1.0)
    ):
        self._x_value_range = x_value_range
        """
        The range of values that will be applied to 
        transform the `x` value obtained (which is
        internally normalized) into the real expected
        value.
        """
        self._y_value_range = y_value_range
        """
        The range of values that will be applied to 
        transform the `y` value obtained (which is
        internally normalized) into the real expected
        value.
        """
        self._nodes: list[CurveNode] = []
        """
        *For internal use only*

        The nodes in the curve as they were added to it.
        """
        self._nodes_ordered: Union[list[CurveNode], None] = None
        """
        *For internal use only*

        The list of nodes but ordered by the `x` axis from
        left to right.
        """

    def get_node_at(
        self,
        x: float
    ) -> Union[CurveNode, None]:
        """
        Get the node, if existing, at the `x` position
        provided.
        """
        return next(
            (
                node
                for node in self.nodes
                if node.x == x
            ),
            None
        )

    def add_node(
        self,
        x: float,
        y: float
    ) -> 'CurveDefinition':
        """
        Add a new node to the `x` provided with the `y`
        associated value if there is no other node 
        including that `x` value.

        This will clean the cache.
        """
        if self.get_node_at(x) is not None:
            raise Exception('There is a node in the `x` position provided.')
        
        self._nodes.append(CurveNode(x, y))
        self._nodes_ordered = None

        return self
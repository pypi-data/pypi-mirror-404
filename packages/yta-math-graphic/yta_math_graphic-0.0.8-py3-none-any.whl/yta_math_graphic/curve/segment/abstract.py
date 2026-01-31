from yta_math_graphic.curve.node import CurveNode
from abc import ABC


class CurveSegment(ABC):
    """
    A segment of a curve, including 2 nodes and an
    easing function to define the way we interpolate
    the values in between the 2 nodes.
    """

    @property
    def x_min(
        self
    ) -> float:
        """
        The minimum `x` value in the segment.
        """
        return min(
            (
                node.x
                for node in [self.left_node, self.right_node]
            )
        )
    
    @property
    def x_max(
        self
    ) -> float:
        """
        The maximum `x` value in the segment.
        """
        return max(
            (
                node.x
                for node in [self.left_node, self.right_node]
            )
        )
    
    @property
    def y_min(
        self
    ) -> float:
        """
        The minimum `y` value in the segment.
        """
        return min(
            (
                node.y
                for node in [self.left_node, self.right_node]
            )
        )
    
    @property
    def y_max(
        self
    ) -> float:
        """
        The maximum `y` value in the segment.
        """
        return max(
            (
                node.y
                for node in [self.left_node, self.right_node]
            )
        )
    
    @property
    def distance(
        self
    ) -> float:
        """
        The distance of this segment, considering it as the
        absolute distance in between the two `x` values.
        This value is useful when we need to calculate a
        non-uniform segment distribution.

        The formula:
        ```
        abs(self.x_max - self.x_min)
        ```
        """
        return abs(self.x_max - self.x_min)
    
    def __init__(
        self,
        left_node: 'CurveNode',
        right_node: 'CurveNode',
        easing_function: 'EasingFunction'
    ):
        # TODO: Validate (?)
        # TODO: Maybe 'left' and 'right' is not the best
        # because if we accept unordered, when plotting
        # the 'left' it could be drawn on the right...
        self.left_node: 'CurveNode' = left_node
        """
        The node that is in the left side of the segment.
        """
        self.right_node: 'CurveNode' = right_node
        """
        The node that is in the right side of the segment.
        """
        self._easing_function: 'EasingFunction' = easing_function
        """
        *For internal use only*

        The easing function that will be applied when
        calculating the value in between the 2 nodes.
        """

    def evaluate(
        self,
        progress_local: float
    ) -> float:
        """
        Get the value associated to the local progress
        value provided as `progress_local`, applying
        the easing function defined for this instance.

        The `progress_local` must be a value in the
        `[0.0, 1.0]` range.

        The formula:
        - `self.left_node.y + t * (self.right_node.y - self.left_node.y)`
        """
        # We transform the `t` based on the easing function
        t = self._easing_function(progress_local)

        return self.left_node.y + t * (self.right_node.y - self.left_node.y)

    def get_weight(
        self,
        total_distance: float
    ) -> float:
        """
        Get the weight of this segment based on the 
        `total_distance` of the curve and the distance of
        this segment.

        This method is useful when calculating a 
        proportional distribution in which each segment's
        is different according to its own distance.

        The formula:
        - `self.distance / total_distance`
        """
        return self.distance / total_distance
    
    def is_x_contained(
        self,
        x: float
    ) -> bool:
        """
        Check if the `x` value provided is in between the
        2 nodes of this segment.

        The formula:
        - `self.x_min <= x < self.x_max`
        """
        return self.x_min <= x < self.x_max
    
    def get_progress_local(
        self,
        x: float
    ) -> float:
        """
        Get the local progress of the `x` value provided
        based on the internal distance of the segment.

        The `x` value must be contained in between the
        2 nodes, excluding the one on the right.
        
        The formula:
        - `(x - self.x_min) / self.distance`
        """
        if not self.is_x_contained(x):
            raise Exception('The "x" value provided does not belong to this segment.')
        
        return (x - self.x_min) / self.distance

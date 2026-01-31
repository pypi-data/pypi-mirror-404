from yta_math_graphic.motion_graph.node import MotionNode
from yta_math_easings import LinearEasing
from yta_math_interpolation import LinearInterpolation
from yta_validation.parameter import ParameterValidator
from dataclasses import dataclass


@dataclass
class MotionSegment:
    """
    A segment within a `MotionGraph` built by 2
    nodes that are considered the start and the
    end of the segment and the positions in
    between are calculated based on an easing
    function.

    The `node_start` and the `node_end` can be
    at the same position.
    """

    @property
    def duration(
        self
    ) -> float:
        """
        The amount of time (in seconds) that takes to
        travel the distance in x from the `node_start`
        to the `node_end`, that is defined in the
        `node_end` instance.
        """
        return self.node_end.duration

    def __init__(
        self,
        node_start: MotionNode,
        node_end: MotionNode,
        easing_function: 'EasingFunction' = LinearEasing(),
        interpolation_function: 'InterpolationFunction' = LinearInterpolation()
    ):
        ParameterValidator.validate_mandatory_instance_of('node_start', node_start, MotionNode)
        ParameterValidator.validate_mandatory_instance_of('node_end', node_end, MotionNode)

        self.node_start: MotionNode = node_start
        """
        The node in which the segment starts.
        """
        self.node_end: MotionNode = node_end
        """
        The node in which the segment ends.
        """
        self._easing_function: 'EasingFunction' = easing_function
        """
        *For internal use only*

        The easing function that will be applied when
        calculating the value in between the 2 nodes
        of this motion segment.
        """
        self._interpolation_function: 'InterpolationFunction' = interpolation_function
        """
        *For internal use only*

        The interpolation function that will be applied
        to determine the path to follow in between the
        2 nodes of this motion segment.
        """

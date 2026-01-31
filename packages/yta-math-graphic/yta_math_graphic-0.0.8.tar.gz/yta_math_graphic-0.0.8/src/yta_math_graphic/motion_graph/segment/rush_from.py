from yta_math_graphic.motion_graph.segment.abstract import MotionSegment
from yta_math_graphic.motion_graph.node import MotionNode
from yta_math_easings import RushFromEasing
from yta_math_interpolation.abstract import InterpolationFunction


class RushFromMotionSegment(MotionSegment):
    """
    A segment within a `MotionGraph` built by 2
    nodes that are considered the start and the
    end of the segment and the easing function
    applied in between is RushFrom.

    The `node_start` and the `node_end` can be
    at the same position.
    """

    def __init__(
        self,
        node_start: MotionNode,
        node_end: MotionNode,
        interpolation_function: InterpolationFunction
    ):
        super().__init__(
            node_start = node_start,
            node_end = node_end,
            easing_function = RushFromEasing(),
            interpolation_function = interpolation_function
        )
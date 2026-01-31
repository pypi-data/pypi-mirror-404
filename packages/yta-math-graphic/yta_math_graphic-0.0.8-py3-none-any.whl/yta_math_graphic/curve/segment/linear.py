from yta_math_graphic.curve.segment.abstract import CurveSegment
from yta_math_easings import LinearEasing


class LinearCurveSegment(CurveSegment):
    """
    A curve segment that is based on a linear easing
    function to calculate the `y` value.
    """

    def __init__(
        self,
        left_node: 'CurveNode',
        right_node: 'CurveNode'
    ):
        super().__init__(
            left_node = left_node,
            right_node = right_node,
            easing_function = LinearEasing()
        )
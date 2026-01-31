from yta_math_graphic.curve.node import CurveNode
from yta_math_graphic.curve.segment.abstract import CurveSegment
from yta_math_graphic.curve.segment import LinearCurveSegment, SmoothererCurveSegment


class SegmentFactory:
    """
    A factory to create curve segments.
    """

    def create(
        self,
        left_node: CurveNode,
        right_node: CurveNode
    ) -> CurveSegment:
        """
        Create a new `CurveSegment` including the `left_node`
        and the `right_node` provided.
        """
        # TODO: Why is it only Linear here and how to
        # make it customizable (?)
        return SmoothererCurveSegment(
            left_node = left_node,
            right_node = right_node
        )
        # return LinearCurveSegment(
        #     left_node = left_node,
        #     right_node = right_node
        # )

from yta_math_graphic.curve.segment.distribution.abstract import WeightedSegmentDistribution
from yta_math_graphic.curve.segment.abstract import CurveSegment


class UniformWeightedSegmentDistribution(WeightedSegmentDistribution):
    """
    A weighted segment distribution in which each
    segment's weight is the same, ignoring the specific
    distance in each segment.
    """

    @staticmethod
    def get_weights(
        segments: list['CurveSegment']
    ) -> list[float]:
        number_of_segments = len(segments)

        return [1.0 / number_of_segments] * number_of_segments
        
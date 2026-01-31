from yta_math_graphic.curve.segment.distribution.abstract import WeightedSegmentDistribution
from yta_math_graphic.curve.segment.abstract import CurveSegment


class ProportionalSegmentDistribution(WeightedSegmentDistribution):
    """
    A weighted segment distribution in which seach segment
    weights are proportional to their real distance, which
    means that the longer segments will have more weight
    when calculating the distribution.
    """

    @staticmethod
    def get_weights(
        segments: list['CurveSegment']
    ) -> list[float]:
        total_distance = sum(segment.distance for segment in segments)

        return [
            segment.get_weight(total_distance)
            for segment in (segments)
        ]

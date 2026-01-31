from yta_math_graphic.curve.segment.distribution.uniform import UniformWeightedSegmentDistribution
from yta_math_graphic.curve.segment.distribution.proportional import ProportionalSegmentDistribution


"""
TODO: Continue implementing new options:
1. Ease / EasingSegment
    EaseIn
    EaseOut
    EaseInOut
    SmoothStep
    S-Curve
2. BezierCurveSegment
3. Hermite / CubicSegment
4. Step / HoldSegment
5. Extrapolated / OvershootSegment
"""

__all__ = [
    'UniformWeightedSegmentDistribution',
    'ProportionalSegmentDistribution'
]
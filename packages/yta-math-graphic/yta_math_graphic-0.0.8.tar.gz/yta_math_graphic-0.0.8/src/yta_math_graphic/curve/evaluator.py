from yta_math_graphic.curve.definition import CurveDefinition
from yta_math_graphic.curve.segment.distribution.abstract import WeightedSegmentDistribution
from yta_math_graphic.curve.segment.factory import SegmentFactory


class CurveEvaluator:
    """
    The evaluator of a curve, which is able to
    calculate the values according to the progress
    or `x` value provided.
    """

    @property
    def _nodes(
        self
    ) -> list['CurveNode']:
        """
        The nodes of the curve, ordered by the `x` value.
        """
        return self._definition.nodes

    def __init__(
        self,
        definition: CurveDefinition,
        distribution: WeightedSegmentDistribution,
        segment_factory: SegmentFactory
    ):
        self._definition = definition
        """
        *For internal use only*

        The definition of the curve.
        """
        self._segments = [
            segment_factory.create(self._nodes[i], self._nodes[i + 1])
            for i in range(len(self._nodes) - 1)
        ]
        """
        *For internal use only*

        The segments of the curve, created based on the
        `segment_factory` provided, and including the
        nodes ordered by the `x` value.
        """
        # TODO: Maybe rename to '_weighted_distribution'
        self._distribution = distribution
        """
        *For internal use only*

        The distribution of the segments to apply in the
        curve.
        """

    def evaluate(
        self,
        progress_normalized: float
    ) -> float:
        """
        Get the value associated to the global
        `progress_normalized` provided, that will be
        transformed into the `y` value associated to it.

        The value returned will be the real value according
        to the `value_range` set in the `Curve` instance.
        """
        y_normalized = self._distribution.get_y_from_progress(
            progress_normalized = progress_normalized,
            segments = self._segments
        )

        # We force it to be denormalized
        do_denormalize: bool = True

        return (
            self._denormalize_y(y_normalized)
            if do_denormalize else
            y_normalized
        )
    
    def evaluate_at(
        self,
        x: float
    ) -> float:
        """
        Get the value associated to the `x` real value
        provided, that will be transformed into the `y`
        value associated to it.

        The value returned will be the real value according
        to the `value_range` set in the `Curve` instance.
        """
        x_normalized = self._normalize_x(x)

        y_normalized = self._distribution.get_y_from_x(
            x = x_normalized,
            segments = self._segments
        )

        # We force it to be denormalized
        do_denormalize: bool = True

        return (
            self._denormalize_y(y_normalized)
            if do_denormalize else
            y_normalized
        )
    
    # Not used by now
    def _normalize_x(
        self,
        x: float
    ) -> float:
        """
        *For internal use only*

        Transform the not normalized `x` value into the
        normalized value according to the value range
        defined for the curve.
        """
        return _normalize(
            value = x,
            value_range = self._definition._x_value_range
        )
    
    def _denormalize_x(
        self,
        x_normalized: float
    ) -> float:
        """
        *For internal use only*

        Transform the `x_normalized` value into the real
        value according to the value range defined for the
        curve.
        """
        return _denormalize(
            value = x_normalized,
            value_range = self._definition._x_value_range
        )

    # Not used by now
    def _normalize_y(
        self,
        y: float
    ) -> float:
        """
        *For internal use only*

        Transform the not normalized `y` into the
        normalized value according to the value range
        defined for the curve.
        """
        return _normalize(
            value = y,
            value_range = self._definition._y_value_range
        )
    
    def _denormalize_y(
        self,
        y_normalized: float
    ) -> float:
        """
        *For internal use only*

        Transform the `y_normalized` value into the real
        value according to the value range defined for the
        curve.
        """
        return _denormalize(
            value = y_normalized,
            value_range = self._definition._y_value_range
        )
    
def _normalize(
    value: float,
    value_range: tuple[float, float]
) -> float:
    """
    *For internal use only*

    Transform the not normalized `value` into the
    normalized value according to the `value_range`
    provided.
    """
    min_value, max_value = value_range

    return (value - min_value) / (max_value - min_value)
    
def _denormalize(
    value: float,
    value_range: tuple[float, float]
) -> float:
    """
    *For internal use only*

    Transform the normalized `value` into the real
    value according to the `value_range` provided.
    """
    min_value, max_value = value_range

    return min_value + value * (max_value - min_value)
        


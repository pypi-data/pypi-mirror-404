from yta_math_graphic.curve.segment.abstract import CurveSegment
from yta_validation.parameter import ParameterValidator
from abc import ABC, abstractmethod
from typing import Union


class WeightedSegmentDistribution(ABC):
    """
    A segment distribution in which the different
    segments have different weights.

    The distribution of the curve, that defines how
    a global `progress_normalized` value is turned into this:
    - `segment_index`
    - `progress_local`
    """

    @abstractmethod
    def get_weights(
        self,
        segments: list['CurveSegment']
    ) -> list[float]:
        """
        Get the weights for the different segments according
        to the curve segments provided.

        This method must be implemented by each specific
        class.
        """
        pass

    def get_y_from_progress(
        self,
        progress_normalized: float,
        segments: list[CurveSegment]
    ) -> float:
        """
        Transform the global `progress_normalized`
        provided into the `y` normalized value associated
        to it, looking for the segments (inside of the
        `segments` list provided) the progress belongs
        to and calculating it.
        """
        segment, progress_local_normalized = self._get_segment_and_local_progress_from_progress(
            progress_normalized = progress_normalized,
            segments = segments
        )

        return segment.evaluate(progress_local_normalized)

    def get_y_from_x(
        self,
        x: float,
        segments: list[CurveSegment]
    ) -> float:
        """
        Transform the `x` normalized value into the `y` 
        normalized value associated to that value, looking
        for the exact segment that contains it (into the
        `segments` provided) and evaluating the local
        progress that is calculated according to the `x`
        given.
        """
        segment, progress_local_normalized = self._get_segment_and_local_progress_from_x(
            x = x,
            segments = segments
        )

        return segment.evaluate(progress_local_normalized)

    def _get_segment_and_local_progress_from_x(
        self,
        x: float,
        segments: list[CurveSegment]
    ) -> tuple[CurveSegment, float]:
        """
        Transform the `x` normalized value provided
        into the local and normalized progress and 
        the corresponding segment, returninga tuple
        containing:
        - `segment`
        - `progress_local_normalized`
        """
        segment = self._get_segment_from_x(
            x = x,
            segments = segments
        )

        if segment is None:
            raise Exception(f'No segment for the x={str(x)} provided.')

        x0 = segment.x_min
        x1 = segment.x_max

        progress_local_normalized = (x - x0) / (x1 - x0)

        return (segment, progress_local_normalized)
    
    def _get_segment_and_local_progress_from_progress(
        self,
        progress_normalized: float,
        segments: list[CurveSegment]
    ) -> tuple[CurveSegment, float]:
        """
        Get the segment the provided global `progress_normalized`
        belongs to, and also de local progress according to that
        segment.

        This method will return a tuple containing:
        - `segment`
        - `progress_local`
        """
        ParameterValidator.validate_number_between('progress_normalized', progress_normalized, 0.0, 1.0)
        ParameterValidator.validate_mandatory_list_of_these_instances('segments', segments, CurveSegment)

        segment_weights = self.get_weights(segments)

        total_weight = sum(segment_weights)
        if total_weight <= 0.0:
            raise Exception('Total segment weight must be > 0')

        target = progress_normalized * total_weight
        accumulated_weight = 0.0

        for index, weight in enumerate(segment_weights):
            next_accumulated_weight = accumulated_weight + weight

            if (
                target <= next_accumulated_weight or
                index == len(segment_weights) - 1
            ):
                # We found the segment corresponding to the global
                # `progress_normalized` provided
                local = target - accumulated_weight
                progress_local = (
                    local / weight
                    if weight > 0 else
                    0.0
                )

                return segments[index], progress_local

            accumulated_weight = next_accumulated_weight

        return (segments[-1], 1.0)

    def _get_segment_from_x(
        self,
        x: float,
        segments: list[CurveSegment]
    ) -> Union[CurveSegment, None]:
        """
        *For internal use only*

        Get the segment in which the `x` value provided fits,
        that is by applying the `[x_min, x_max)` range for
        all the segments and `[x_min, x_max]` for the last
        one.
         
        For the last segment:
        - `if segment.x_min <= x <= segment.x_max`

        For the rest:
        - `if segment.x_min <= x < segment.x_max`
        """
        for i, segment in enumerate(segments):
            if i == len(segments) - 1:
                if segment.x_min <= x <= segment.x_max:
                    return segment
            else:
                if segment.x_min <= x < segment.x_max:
                    return segment
                
        return None
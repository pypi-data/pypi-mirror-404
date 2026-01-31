from yta_math_graphic.motion_graph.node import MotionNode
from yta_math_graphic.motion_graph.segment.abstract import MotionSegment
from yta_math_graphic.motion_graph.segment import LinearMotionSegment, SmoothMotionSegment, SmoothStepMotionSegment, SmootherStepMotionSegment, SmoothererStepMotionSegment, RushIntoMotionSegment, RushFromMotionSegment
from yta_math_easings.enums import EasingFunctionName
from yta_math_easings.abstract import EasingFunction
from yta_math_interpolation.abstract import InterpolationFunction
from yta_math_interpolation.enums import InterpolationFunctionName
from typing import Union


class MotionSegmentFactory:
    """
    A factory to create Motion Graph segments based
    on the initial configuration.
    """

    def __init__(
        self,
        easing_function_name: Union[EasingFunctionName, str] = EasingFunctionName.LINEAR,
        interpolation_function_name: Union[InterpolationFunctionName, str] = InterpolationFunctionName.LINEAR
    ):
        easing_function_name = EasingFunctionName.to_enum(easing_function_name)
        interpolation_function_name = InterpolationFunctionName.to_enum(interpolation_function_name)

        self._easing_function_class: MotionSegment = {
            EasingFunctionName.LINEAR: LinearMotionSegment,
            EasingFunctionName.SMOOTH: SmoothMotionSegment,
            EasingFunctionName.SMOOTH_STEP: SmoothStepMotionSegment,
            EasingFunctionName.SMOOTHER_STEP: SmootherStepMotionSegment,
            EasingFunctionName.SMOOTHERER_STEP: SmoothererStepMotionSegment,
            EasingFunctionName.RUSH_INTO: RushIntoMotionSegment,
            EasingFunctionName.RUSH_FROM: RushFromMotionSegment
            # TODO: We need more
        }.get(easing_function_name, None)
        """
        *For internal use only*

        The class that will be used to create the easing
        function instance.
        """

        if self._easing_function_class is None:
            raise Exception(f'The easing function "{easing_function_name.value}" is not available.')

        self._interpolation_function_class: 'EasingFunction' = InterpolationFunction.get(interpolation_function_name)
        """
        *For internal use only*

        The class that will be used to create the interpolation
        function instance.
        """

    def create(
        self,
        node_start: MotionNode,
        node_end: MotionNode
    ) -> MotionSegment:
        """
        Create a new motion segment instance including the
        `node_start` and the `node_end` nodes.
        """
        return self._easing_function_class(
            node_start = node_start,
            node_end = node_end,
            interpolation_function = self._interpolation_function_class()
        )
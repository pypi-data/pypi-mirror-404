from yta_math_graphic.curve.segment.distribution.abstract import WeightedSegmentDistribution
from yta_math_graphic.curve.segment.distribution.uniform import UniformWeightedSegmentDistribution
from yta_math_graphic.curve.segment.factory import SegmentFactory
from yta_math_graphic.curve.evaluator import CurveEvaluator
from yta_math_graphic.curve.definition import CurveDefinition
from yta_programming.decorators.requires_dependency import requires_dependency
from yta_validation.parameter import ParameterValidator
from typing import Union


class Curve:
    """
    A curve, representing both `x` and `y` axis in a
    normalized range (`[0.0, 1.0]`).

    There are no mandatory nodes for this curve, which
    means that it could have not any node at the `x=0.0`
    nor `x=1.0`. Check `ParameterCurve` if you want them
    to be mandatory.
    """
    
    @property
    def nodes(
        self
    ) -> list['CurveNode']:
        """
        The list of nodes ordered by the `x` value.
        """
        return self._definition.nodes
    
    @property
    def segments(
        self
    ) -> list['CurveSegment']:
        """
        The list of segments ordered by the `x` value.
        """
        return self._evaluator._segments
    
    @property
    def x_min(
        self
    ) -> Union[float, None]:
        """
        The minimum `x` value. Useful value to use for
        the axis and because it is where the progress
        starts.
        """
        return self._definition.x_min
    
    @property
    def x_max(
        self
    ) -> Union[float, None]:
        """
        The maximum `x` value. Useful value to use for
        the axis and because it is where the progress
        ends.
        """
        return self._definition.x_max
    
    @property
    def y_min(
        self
    ) -> Union[float, None]:
        """
        The minimum `y` value.
        """
        return self._definition.y_min
    
    @property
    def y_max(
        self
    ) -> Union[float, None]:
        """
        The maximum `y` value.
        """
        return self._definition.y_max
    
    @property
    def distance(
        self
    ) -> Union[float, None]:
        """
        The distance (normalized) of the whole curve.
        """
        return self._definition.distance
    
    @property
    def x_value_range(
        self
    ) -> tuple[float, float]:
        """
        The range of values that will be applied to
        transform the `x` value obtained (which is
        internally normalized) into the real expected
        value.
        """
        return self._definition._x_value_range

    @property
    def y_value_range(
        self
    ) -> tuple[float, float]:
        """
        The range of values that will be applied to
        transform the `y` value obtained (which is
        internally normalized) into the real expected
        value.
        """
        return self._definition._y_value_range

    def __init__(
        self,
        x_value_range: tuple[float, float] = (0.0, 1.0),
        y_value_range: tuple[float, float] = (0.0, 1.0),
        distribution: WeightedSegmentDistribution = UniformWeightedSegmentDistribution(),
        segment_factory: SegmentFactory = SegmentFactory(),
    ):
        """
        The value range is the range of values in which 
        each axis will be forced to belong to and all
        the values will be in.

        The curve works internally with normalized values
        (in the `[0.0, 1.0]` range), but they are
        denormalized to the real values that fit this
        range to be able to use it in a real environment.

        If you want to represent a parameter, you can use
        `y_value_range=(0, 255)` and all the values will be
        inside that range, being transformed like this:
        - `0.0 -> 0`
        - `1.0 -> 255`
        """
        ParameterValidator.validate_mandatory_subclass_of('distribution', distribution, WeightedSegmentDistribution)
        ParameterValidator.validate_mandatory_instance_of('segment_factory', segment_factory, SegmentFactory)
        # TODO: Validate 'x_value_range'
        # TODO: Validate 'y_value_range'
        
        self._definition = CurveDefinition(
            x_value_range = x_value_range,
            y_value_range = y_value_range
        )
        """
        *For internal use only*

        The definition of the curve.
        """
        self._distribution = distribution
        """
        *For internal use only*

        The distribution of the curve.
        """
        self._segment_factory = segment_factory
        """
        *For internal use only*

        The segment factory of the curve.
        """
        self._evaluator: CurveEvaluator = None
        """
        *For internal use only*

        The evaluator of the curve.
        """

        self._reset_cache()

    def add_node(
        self,
        x: float,
        y: float
    ) -> 'Curve':
        """
        Add a new node to the real `x` provided with the
        also real `y` value associated to it. 
        
        The `x` and `y` values provided must be inside
        the value ranges provided for this instance.
        """
        ParameterValidator.validate_mandatory_number_between('x', x, self.x_value_range[0], self.x_value_range[1])
        ParameterValidator.validate_mandatory_number_between('y', y, self.y_value_range[0], self.y_value_range[1])

        # Normalize the 'y' before storing it
        x = self._evaluator._normalize_x(x)
        y = self._evaluator._normalize_y(y)

        self._definition.add_node(x, y)
        # Invalidate cache
        self._evaluator = None
        self._reset_cache()

        return self

    def _reset_cache(
        self
    ) -> 'Curve':
        """
        *For internal use only*

        Reset the cache by reseting the evaluator.
        """
        self._evaluator = CurveEvaluator(
            self._definition,
            self._distribution,
            self._segment_factory
        )

        return self

    def evaluate(
        self,
        progress_normalized: float
    ) -> float:
        """
        Get the real `y` value associated to the global
        `progress_normalized` provided.

        The value associated will be inside the value
        range provided for this curve as it is a real
        value.
        """
        if self._evaluator is None:
            self._reset_cache()

        return self._evaluator.evaluate(
            progress_normalized = progress_normalized
        )
    
    def evaluate_at(
        self,
        x: float
    ) -> float:
        """
        Get the real `y` value associated to the real `x`
        value provided.

        The value associated will be inside the value
        range provided for this curve.
        """
        if self._evaluator is None:
            self._reset_cache()

        return self._evaluator.evaluate_at(
            x = x
        )

    @requires_dependency('matplotlib', 'yta_math_graphic', 'matplotlib')
    def plot(
        self,
        number_of_samples_per_segment: int = 100,
        do_draw_nodes: bool = True,
        do_draw_segments: bool = True
    ) -> None:
        """
        *Requires optional dependency `matplotlib`*

        Displays the curve in a normalized space
        `[0.0, 1.0] -> [0.0, 1.0]`.
        """
        import matplotlib.pyplot as plt
        import numpy as np

        plt.xlim(self.x_value_range[0], self.x_value_range[1])
        plt.ylim(self.y_value_range[0], self.y_value_range[1])
        plt.axhline(0.0, linewidth = 1)
        plt.axvline(0.0, linewidth = 1)
        plt.grid(True)

        nodes = self.nodes

        if do_draw_segments:
            for node_left, node_right in zip(nodes[:-1], nodes[1:]):
                xs = np.linspace(node_left.x, node_right.x, number_of_samples_per_segment)
                ys = [
                    self.evaluate_at(self._evaluator._denormalize_x(x))
                    for x in xs
                ]
                # Denormalize to print
                xs = [
                    self._evaluator._denormalize_x(x)
                    for x in xs
                ]
                plt.plot(xs, ys, linewidth = 2)

        if do_draw_nodes:
            x_nodes = [
                self._evaluator._denormalize_x(node.x)
                for node in nodes
            ]
            y_nodes = [
                self._evaluator._denormalize_y(node.y)
                for node in nodes
            ]

            plt.scatter(
                x_nodes,
                y_nodes,
                s = 80,
                facecolors = 'white',
                edgecolors = 'black',
                zorder = 3
            )

        plt.xlabel('Progress (normalized)')
        plt.ylabel('Value (normalized)')
        plt.title('Curve')

        plt.show()


# TODO: Maybe move to the editor instead (?)
class ParameterCurve(Curve):
    """
    A curve that always includes values for the initial
    (`x_normalized=0.0`) and final (`x_normalized=1.0`)
    nodes, forcing it to have real values for all the
    values in the internal and normalized range
    `[0.0, 1.0]`.

    It will be initialized with 2 mandatory nodes, at
    `x=0.0` and at `x=1.0` having the values provided
    in the `__init__` method.

    This curve is perfect to be applied in edition to
    set all the parameter values we want.
    """

    def __init__(
        self,
        y_start: float,
        y_end: float,
        x_value_range: tuple[float, float] = (0.0, 1.0),
        y_value_range: tuple[float, float] = (0.0, 1.0),
        distribution: WeightedSegmentDistribution = UniformWeightedSegmentDistribution(),
        segment_factory: SegmentFactory = SegmentFactory(),
    ):
        """
        The `y_start` and `y_end` values must be according
        to the `y_value_range` provided.
        """
        super().__init__(
            x_value_range = x_value_range,
            y_value_range = y_value_range,
            distribution = distribution,
            segment_factory = segment_factory
        )

        # We force to add the first and last node
        self.add_node(
            x = x_value_range[0],
            y = y_start
        ).add_node(
            x = x_value_range[1],
            y = y_end
        )
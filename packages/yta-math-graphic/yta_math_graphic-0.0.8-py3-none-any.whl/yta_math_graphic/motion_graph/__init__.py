from yta_math_graphic.motion_graph.segment.abstract import MotionSegment
from yta_math_graphic.motion_graph.segment.factory import MotionSegmentFactory
from yta_math_graphic.motion_graph.node import MotionNode
from yta_programming.decorators.requires_dependency import requires_dependency
from yta_validation.parameter import ParameterValidator
from typing import Union


class MotionGraph:
    """
    A graph that defines how an element will be
    moving through the scene, including the time
    spent to reach each node of the trajectory.

    The first node is always needed as the start
    of this graph.
    """

    @property
    def x_min(
        self
    ) -> Union[float, None]:
        """
        The minimum `x` value.
        """
        return min(
            (
                node.x
                for node in self.nodes
            ),
            default = None
        )
    
    @property
    def y_min(
        self
    ) -> Union[float, None]:
        """
        The minimum `y` value.
        """
        return min(
            (
                node.y
                for node in self.nodes
            ),
            default = None
        )
    
    @property
    def x_max(
        self
    ) -> Union[float, None]:
        """
        The maximum `x` value.
        """
        return max(
            (
                node.x
                for node in self.nodes
            ),
            default = None
        )
    
    @property
    def y_max(
        self
    ) -> Union[float, None]:
        """
        The maximum `y` value.
        """
        return max(
            (
                node.y
                for node in self.nodes
            ),
            default = None
        )

    @property
    def duration(
        self
    ) -> float:
        """
        The total duration of this `MotionGraph`, which is
        the sum of the duration of all the segments 
        included on it.
        """
        return sum(
            segment.duration
            for segment in self.segments
        )
    
    def __init__(
        self,
        start_position: tuple[int, int],
        segment_factory: MotionSegmentFactory = MotionSegmentFactory()
    ):
        # TODO: Validate 'start_position' (?)

        self._segment_factory = segment_factory
        """
        The specific factory to create the segments based on
        the configuration provided.
        """
        self.nodes: list[MotionNode] = [
            # The first node must be always included
            MotionNode(
                x = start_position[0],
                y = start_position[1],
                duration = 0.0
            )
        ]
        """
        The list of motion nodes that define this `MotionGraph`
        instance, ordered as they were added (that is also how
        they have to be evaluated).
        """
        self.segments: list[MotionSegment] = []
        """
        The list of segments that include the different
        nodes of this `MotionGraph` instance.
        """

    def add_node(
        self,
        position: tuple[float, float],
        duration: float
    ) -> 'MotionGraph':
        """
        Add a new node that will be in the `position` provided
        and will take the `duration` time provided (in seconds)
        to reach from the previous one.
        """
        self.nodes.append(
            MotionNode(
                x = position[0],
                y = position[1],
                duration = duration
            )
        )

        # We update the 'segments' list
        self.segments.append(
            self._segment_factory.create(
                node_start = self.nodes[-2],
                node_end = self.nodes[-1]
            )
        )

        return self

    # Maybe it is not necessary...
    # def _get_segment_at(
    #     self,
    #     t: float
    # ) -> Union[MotionSegment, None]:
    #     """
    #     Get the segment that includes the `t` time
    #     moment provided.

    #     The `t` time moment must be the range
    #     `[0.0, self.duration]`.
    #     """
    #     ParameterValidator.validate_mandatory_number_between('t', t, 0.0, self.duration)

    #     if t == self.duration:
    #         return self._segments[-1]

    #     t_elapsed = 0.0
    #     for segment in self._segments:
    #         if (t_elapsed + segment.duration) >= t:
    #             t_local = (t - t_elapsed) / segment.duration

    #             return self._lerp(
    #                 start_node = segment.node_start,
    #                 end_node = segment.node_end,
    #                 t_segment = t_local
    #             )
            
    #         t_elapsed += segment.duration
            
    #     # We should never reach this point
    
    def evaluate(
        self,
        t: float
    ) -> MotionNode:
        """
        Get a `MotionNode` indicating the exact position
        according to the global `t` time moment.

        The `t` time moment must be in the range
        `[0.0, self.duration]`.
        """
        ParameterValidator.validate_mandatory_number_between('t', t, 0.0, self.duration)

        if t == self.duration:
            # Is the end so we return the last node
            return self.segments[-1].node_end

        t_elapsed = 0.0
        for segment in self.segments:
            if (t_elapsed + segment.duration) >= t:
                t_segment = (t - t_elapsed)
                t_segment_normalized = t_segment / segment.duration
                """
                We apply the easing function, but this is only
                affecting to the 't', which means to the speed
                of the movement but not the trajectory. We need
                bezier or similar to adjust the trajectory and
                use it in the '._lerp' method that resolves the
                'x'.
                """
                t_segment_normalized = segment._easing_function(t_segment_normalized)

                # We apply the magic 'autocalculated' method by now
                # and will let the user define the path in the future
                interpolated_point = segment._interpolation_function.interpolate_autocalculated(
                    t = t_segment_normalized,
                    point_start = segment.node_start.position,
                    point_end = segment.node_end.position
                )

                # Create new artificial node
                return MotionNode(
                    x = interpolated_point[0],
                    y = interpolated_point[1],
                    duration = t_segment
                )

                # We return a new artificial node in the middle
                # of the segment
                return self._lerp(
                    start_node = segment.node_start,
                    end_node = segment.node_end,
                    t_segment = t_local_normalized
                )
            
            t_elapsed += segment.duration

        # We should never reach this point
    
    # TODO: Maybe this should be moved to the segment
    # but careful because the `t_segment` here has
    # been modified applying the easing function
    # previously
    # TODO: No longer used
    def _lerp(
        self,
        start_node: MotionNode,
        end_node: MotionNode,
        t_segment_normalized: float
    ) -> MotionNode:
        """
        *For internal use only*

        Get a `MotionNode` representing the position in
        which the element should be based on the
        `t_segment_normalized` time moment provided.
        """
        # u = 1 - t_segment
    
        # """
        # The bezier formula is:
        # u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0],
        # u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1],

        # but I don't have p2...
        # """
        # return MotionNode(
        #     x = u*u*start_node.x + 2*u*t_segment*end_node.x + t_segment*t_segment*end_node.x,
        #     y = u*u*start_node.y + 2*u*t_segment*end_node.y + t_segment*t_segment*end_node.y,
        #     duration = t_segment
        # )

        # Linear trajectory
        return MotionNode(
            x = start_node.x + (end_node.x - start_node.x) * t_segment_normalized,
            y = start_node.y + (end_node.y - start_node.y) * t_segment_normalized,
            # TODO: I think this 'duration' shouldn't be normalized
            duration = t_segment_normalized
        )
    
    @requires_dependency('matplotlib', 'yta_math_graphic', 'matplotlib')
    def plot(
        self,
        number_of_samples_per_segment: int = 100,
        do_use_limits: bool = False,
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

        # 1920x1080 scene
        x_lim = (
            (self.x_min, self.x_max)
            if do_use_limits else
            (0, 1920)
        )
        y_lim = (
            (self.y_min, self.y_max)
            if do_use_limits else
            (0, 1080)
        )
        plt.xlim(*x_lim)
        plt.ylim(*y_lim)
        plt.axhline(0.0, linewidth = 1)
        plt.axvline(0.0, linewidth = 1)
        plt.grid(True)

        nodes = self.nodes

        if do_draw_segments:
            positions = [
                self.evaluate(t)
                for t in np.linspace(0.0, self.duration, len(self.segments) * number_of_samples_per_segment)
            ]

            plt.plot(
                [
                    position.x
                    for position in positions
                ], 
                [
                    position.y
                    for position in positions
                ],
                linewidth = 2
            )

        if do_draw_nodes:
            x_nodes = [
                node.x
                for node in nodes
            ]
            y_nodes = [
                node.y
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
from yta_editor_nodes.timeline.parameter.abstract import ParameterSource
from yta_validation.parameter import ParameterValidator
from abc import ABC, abstractmethod
from typing import Union


class TimelineNode(ABC):
    """
    *Abstract class*

    *This class has to be inherited by any class that is
    able to handle some input to obtain an output as a
    result*

    The abstract class of a TimelineNode, which is the
    entity that is able to process some input to return
    an output that can be sent to the next node, and able
    to connect (by storing the references) to the other
    nodes.
    """

    @property
    def has_output_node(
        self
    ) -> bool:
        """
        Boolean flag to indicate if this node has an
        output node or not.
        """
        return self.output_node is not None
    
    @property
    def has_input_node(
        self
    ) -> bool:
        """
        Boolean flag to indicate if this node has an
        input node or not.
        """
        return self.input_node is not None
    
    @property
    def duration(
        self
    ) -> float:
        """
        The duration of the timeline node, in seconds.

        The formula:
        - `self.t_end - self.t_start`
        """
        return self.t_end - self.t_start

    def __init__(
        self,
        name: str,
        t_start: Union[int, float, 'Fraction'],
        t_end: Union[int, float, 'Fraction'],
        parameters_sources: dict[str, ParameterSource] = {}
    ):
        ParameterValidator.validate_mandatory_string('name', name, do_accept_empty = False)
        ParameterValidator.validate_mandatory_positive_number('t_start', t_start, do_include_zero = True)
        ParameterValidator.validate_mandatory_positive_number('t_end', t_end, do_include_zero = False)
        # TODO: Validate 'parameters_sources' as dict of 
        # 'str': ParameterSource

        if t_end < t_start:
            raise Exception('The "t_end" parameter provided must be greater or equal to the "t_start" parameter.')

        self.name: str = name
        """
        Just a simple name for the node.
        """
        self.is_enabled: bool = True
        """
        Boolean flag to indicate if the node is enabled or not,
        which means that it will not be working if not enabled.
        Basically, if it is on or off.
        """
        self.t_start: float = t_start
        """
        The 't' time moment in which the TimelineNode must start
        being applied (including it).
        """
        self.t_end: float = t_end
        """
        The `t` time moment in which the TimelineNode must stop
        being applied (excluding it).

        TODO: The `end` we receive here could be
        greater than the actual end of the media
        in which the TimedNode will be applied,
        but it seems to be working correctly as
        we will never receive a `t` from that
        media that is out of its own bounds...
        """
        self.parameters_sources: dict[str, ParameterSource] = parameters_sources
        """
        A dict including the `key` of the parameter and
        its source.
        """

        self.input_node: Union['TimelineNode', None] = None
        """
        The node that is connected to this one as an
        input, so the output of that previous node will
        be passed as the input for this one.
        """
        self.output_node: Union['TimelineNode', None] = None
        """
        This node is connected as the input of another
        one that is after this. The output of this one
        will be sent as the input for that one.
        """
        self._cached_output: Union['np.ndarray', 'moderngl.Texture', None] = None
        """
        The output, but cached, so when it is generated
        it is stored here.
        """

    def _get_t(
        self,
        t: Union[int, float, 'Fraction']
    ) -> float:
        """
        Obtain the `t` time moment relative to the
        effect duration.

        Imagine `start=3` and `end=5`, and we receive 
        a `t=4`. It is inside the range, so we have
        to apply the effect, but as the effect
        lasts from second 3 to second 5 (`duration=2`),
        the `t=4` is actually a `t=1` for the effect
        because it is the time elapsed since the
        effect started being applied, that was on the 
        second 3.

        The formula:
        - `t - self.t_start`
        """
        return t - self.t_start
    
    def enable(
        self
    ) -> 'TimelineNode':
        """
        Enable the node by setting the internal flag to
        `True`, which means that will be working.
        """
        self.is_enabled = True

        return self
    
    def disable(
        self
    ) -> 'Timeline':
        """
        Disable the node by setting the internal flag
        to `False`, which means that will be working not.
        """
        self.is_enabled = False

        return self
    
    def is_active_at(
        self,
        t_timeline: float
    ) -> bool:
        """
        Flag to indicate if the `t_timeline` time moment
        provided is in the range of this TimedNode instance, 
        which means between the `t_start` and the `t_end`,
        and if it is activated or not (on or off).

        The formula:
        - `t_start <= t_timeline < t_end`
        """
        return (
            self.is_enabled and
            self.t_start <= t_timeline < self.t_end
        )

    def connect_to(
        self,
        node: 'TimelineNode'
    ) -> 'TimelineNode':
        """
        Connect the `node` provided to this one as an
        output, and also this one as an input of the
        `node` provided.

        TODO: The connection has to be done with another
        class that inherits from this 'TimelineNode'.
        """
        self.output_node = node
        node.input_node = self

        return self

    def clear_cache(
        self
    ) -> 'TimelineNode':
        """
        Clear the cache of this node, but also for
        the nodes that are outputs of this one, as
        the results would change.
        """
        # TODO: I think this cache is not valid because
        # we are using a `t` and different inputs...
        self._cached_output = None

        self.output_node.clear_cache()

        return self
    
    def _evaluate_parameters(
        self,
        t_timeline: float = 0.0
    ) -> dict[str, any]:
        """
        *For internal use only*

        Evaluate all the parameters for the given `t` time
        moment and obtain the values for that moment.
        """
        parameters_values = {}

        t_local_normalized = self._get_t(t_timeline) / self.duration

        for key, parameter_source in self.parameters_sources.items():
            # TODO: Move this to top
            from yta_editor_nodes.timeline.parameter.evaluation_context import EvaluationContext

            parameters_values[key] = parameter_source.evaluate(
                context = EvaluationContext(
                    # The 't' that will be used internally must be normalized
                    t = t_local_normalized,
                    # TODO: What about all this below (?)
                    frame_index = None,
                    node_outputs = None,
                    curves = None,
                    backend = None
                )
            )

        return parameters_values
    
    def process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        t_timeline: float = 0.0,
        # TODO: Maybe we need 'fps' and 'number_of_frames'
        # to calculate progressions or similar...
        # TODO: I think this has to be gone
        **kwargs
    ) -> Union['moderngl.Texture', 'np.ndarray']:
        """
        Process the `input` by using the `t_timeline` time
        moment provided, that could be necessary for the
        node if it is a dynamic one that depends on this
        value.
        """
        # TODO: Maybe a copy (?)
        output = input

        """
        TODO: This condition is evalulated in the
        TimelineGraph this node belongs to, but we need
        the `t` for some dynamic NodeProcessors
        """
        # if not self.is_active_at(t_timeline):
        #     return result

        # TODO: With simple nodes we don't need the 't' and
        # this is failing if we don't put the **kwargs in
        # our CPU or GPU processors
        # This will be ignored if no needed as we use **kwargs
        parameters_values = self._evaluate_parameters(
            t_timeline = t_timeline
        )

        # This should be 'float32' or 'Texture'
        return self._process(
            input = output,
            t_timeline = t_timeline,
            **parameters_values
            # **kwargs
        )

    @abstractmethod
    def _process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        t_timeline: float,
        **kwargs
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the input and obtain a result as the output.

        This method must be overwritten for every special
        class implementation.
        """
        pass
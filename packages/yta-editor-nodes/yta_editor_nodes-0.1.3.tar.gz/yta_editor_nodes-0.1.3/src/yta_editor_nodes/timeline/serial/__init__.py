from yta_editor_nodes.timeline import TimelineNode
from yta_editor_nodes.timeline.parameter.abstract import ParameterSource
from yta_editor_nodes.timeline.parameter.source.utils import normalize_parameter_sources
from typing import Union


class SerialTimelineNode(TimelineNode):
    """
    A node that is executed from a specific input and
    generates a single output that is sent to the next
    node.

    Check the `.process` method definition of the node
    you add to see the parameters you need to execute
    it and pass them through the `parameters_sources`
    parameter.
    """

    def __init__(
        self,
        # TODO: Put the correct class
        # TODO: Maybe I need the 'node' in the TimelineNode class
        # TODO: Maybe I need a shortcut to 'is_gpu_available'...
        node: 'NodeProcessor',
        name: str,
        t_start: Union[int, float, 'Fraction'],
        t_end: Union[int, float, 'Fraction'],
        parameters_sources: dict[str, ParameterSource] = {}
    ):
        self.node: 'NodeProcessor' = node
        """
        The node to execute and to obtain the output from.
        """
        # Validate the 'parameters_sources' by accepting
        # basic and non iterable types. This will raise
        # exception if not valid
        parameters_sources = normalize_parameter_sources(parameters_sources)

        super().__init__(
            name = name,
            t_start = t_start,
            t_end = t_end,
            parameters_sources = parameters_sources
        )

    def _process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        t_timeline: float,
        **kwargs
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the input and obtain a result as the output.
        """
        t_local = self._get_t(t = t_timeline)

        # Add 't' as dynamic because some NodeProcessor
        # don't actually expect it as parameter
        kwargs['t'] = t_local

        return self.node.process(
            input = input,
            **kwargs
        )
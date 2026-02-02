from yta_editor_nodes.timeline import TimelineNode
from yta_editor_nodes.timeline.serial import SerialTimelineNode
from abc import ABC, abstractmethod
from typing import Union


class _ParallelTimelineNodeAbstract(TimelineNode, ABC):
    """
    The abstract class of the parallel node.

    This class is limited and needs at least 2 nodes
    to be valid.
    """

    def __init__(
        self,
        # TODO: Put the correct class
        # TODO: Maybe I need the 'node' in the TimelineNode class
        # TODO: Maybe I need a shortcut to 'is_gpu_available'...
        name: str,
        nodes: list[SerialTimelineNode]
    ):
        if len(nodes) < 2:
            raise Exception('A ParallelTimelineNode needs 2 or more nodes to be created.')
        
        self.nodes: list[SerialTimelineNode] = nodes
        """
        The list of nodes that will be executed in parallel
        to obtain the outputs that will be combined.
        """

        # Calculate the start and end based on nodes
        t_start = min(node.t_start for node in nodes)
        t_end = max(node.t_end for node in nodes)

        super().__init__(
            name = name,
            t_start = t_start,
            t_end = t_end
        )

    def _process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        t_timeline: float,
        **kwargs
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the `input` provided for the `t` time moment
        given and combine the outputs of the different
        internal nodes and return them as output.
        """
        active_nodes = [
            node for node in self.nodes
            if node.is_active_at(t_timeline)
        ]

        # This shouldn't happen as we know that the parallel
        # node itself is not active, but just in case...
        if not active_nodes:
            return input

        if len(active_nodes) == 1:
            return active_nodes[0].process(
                input = input,
                t_timeline = t_timeline,
                **kwargs
            )

        outputs = [
            node.process(
                input = input,
                t_timeline = t_timeline,
                **kwargs
            )
            for node in active_nodes
        ]

        return self._combine_outputs(outputs)
    
    @abstractmethod
    def _combine_outputs(
        self,
        outputs: list[Union['np.ndarray', 'moderngl.Texture']]
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Combine the different `outputs` into a single one.

        This class must be overwritten by every specific
        class implementation.
        """
        # TODO: This must be according to the type
        pass
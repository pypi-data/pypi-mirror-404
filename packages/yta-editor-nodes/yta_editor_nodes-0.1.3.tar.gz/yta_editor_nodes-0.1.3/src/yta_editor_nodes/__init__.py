"""
Our awesome editor module in which we have
all the classes that interact with it and
make it possible.

This is the nodes module, in which we have
all the classes that make the concept work.
"""
from yta_editor_nodes.timeline.utils import is_edition_node
from yta_editor_nodes.timeline.abstract import TimelineNode
from yta_editor_nodes.timeline.serial import SerialTimelineNode
from yta_editor_nodes.timeline.parallel import ParallelTimelineNode
from typing import Union


# TODO: This below is to test the timeline and graphs
class TimelineGraph:
    """
    Graph of nodes (serie and parallel) to process
    the input, handle it and generate an output.

    The graph includes a starting (root) node that
    will begin the process, and maybe other nodes
    connected to it as output nodes.

    The nodes will be interconnected, having a
    `t_start` and `t_end`. The sequence of nodes
    determines the order, and the time range if
    they should modify the input or not.
    """

    def __init__(
        self,
        root_node: Union[SerialTimelineNode, ParallelTimelineNode]
    ):
        self.root_node: Union[SerialTimelineNode, ParallelTimelineNode] = root_node
        """
        The root node in which everything starts.
        """
        self._last_node: Union[SerialTimelineNode, ParallelTimelineNode] = root_node
        """
        *For internal use only*

        The last node we have and the one that will return
        the output.
        """

    def _connect_node_to_last(
        self,
        node: Union[SerialTimelineNode, ParallelTimelineNode]
    ) -> 'TimelineGraph':
        """
        *For internal use only*

        Connect the `node` provided to the last node of this
        timeline, and set this new node as the last one.
        """
        self._last_node.connect_to(node)
        self._last_node = node

        return self

    def add_node(
        self,
        node: Union[SerialTimelineNode, ParallelTimelineNode]
    ) -> 'TimelineGraph':
        """
        Add the `node` provided to the nodes list, connecting
        it (in serie mode) to the last one.
        """
        # TODO: Validate node (?)
        return self._connect_node_to_last(node)

    def add_parallel_node(
        self,
        nodes: list[SerialTimelineNode]
    ):
        """
        Create a `ParallelTimelineNode` with the `nodes` provided
        as parameter and connect it (in serie mode) to the last
        one.
        """
        parallel_node = ParallelTimelineNode(
            name = 'invented',
            # TODO: Validate nodes (?)
            nodes = nodes
        )
        
        return self._connect_node_to_last(parallel_node)

    # TODO: Maybe rename to 'process' (?)
    def render(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        t: float
    ):
        """
        Render the provided `input` at the given `t` time
        moment. The `input` must be the frame that belongs
        to that time moment.

        The different nodes of this instance will be applied
        in order and only if they are enabled and active in
        the `t` time moment provided.
        """
        # TODO: Maybe a '.copy()' (?)
        output = input
        node = self.root_node

        while node is not None:
            if node.is_active_at(
                t_timeline = t
            ):
                output = node.process(
                    input = output,
                    t_timeline = t
                )

            node = node.output_node

        return output
    
__all__ = [
    'TimelineGraph',
    'SerialTimelineNode',
    'ParallelTimelineNode'
]
    

"""
Note for the developer:

A guide to the different types of nodes we will have
when imitating DaVinci Resolve.

TimelineNode (abstracto)
├── ProcessorNode (procesa un solo flujo)
│   ├── EffectNode (filtros, LUTs, shaders…)
│   └── TransitionNode (mezcla entre dos entradas)
│
├── CompositeNode (combina múltiples flujos)
│   ├── SerialTimelineNode (uno tras otro)
│   ├── ParallelTimelineNode (ramas simultáneas)
│   └── LayerNode (capas con blending o máscaras)
│
└── GroupNode (contiene una mini subred de nodos)

"""

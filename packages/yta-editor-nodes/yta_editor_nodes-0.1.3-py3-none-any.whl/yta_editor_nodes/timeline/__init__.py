"""
Module for the nodes that can be applied to
the timeline as edition nodes. These are the
only ones that can be added, and will include
the processing nodes that will make the 
operations.
"""
from yta_editor_nodes.timeline.abstract import TimelineNode
from typing import Union


# TODO: Check the 'new_nodes.py' module for other
# things we should maybe include
# TODO: Other nodes that we are not, by now, handling
"""
This node is to apply changes on the inverse of
the mask of the previous input. TODO: I need to
handle the masks to be able to do this...
"""
# class OutsideNode(TimelineNode):
#     def __init__(self, inside_node: TimelineNode, mask_func):
#         self.inside_node = inside_node
#         self.mask_func = mask_func  # callable: input -> mask (0/1)

#     def process(self, input, **kwargs):
#         mask = self.mask_func(input)
#         inside = self.inside_node.process(input, **kwargs)
#         return input * mask + inside * (1 - mask)

"""
TODO: I don't know the utility of this one...
"""
# class SplitterCombinerNode(TimelineNode):
#     def __init__(self, channels=('R', 'G', 'B')):
#         self.channels = channels

#     def process(self, input, **kwargs):
#         splits = [self._extract_channel(input, c) for c in self.channels]
#         return self._combine_channels(splits)

#     def _extract_channel(self, img, ch):
#         idx = {'R': 0, 'G': 1, 'B': 2}[ch]
#         return img[..., idx:idx+1]

#     def _combine_channels(self, splits):
#         return np.concatenate(splits, axis=-1)

"""
A node that just makes different changes in
serie for the same input.
"""
class CompoundNode(TimelineNode):
    """
    A node that has different nodes that are applied
    to the same input, one after the other, to return
    a single output.

    It is equivalent to use different SerialNode nodes
    in sequence.
    """

    def __init__(
        self,
        nodes: list[TimelineNode]
    ):
        self.nodes: list[TimelineNode] = nodes
        """
        The nodes to execute one after another to obtain 
        the output.
        """

    def process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        **kwargs
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the input and obtain a result as the output.
        """
        result = input

        for node in self.nodes:
            result = node.process(
                input = result,
                **kwargs
            )

        return result
    
class SharedNode(TimelineNode):
    """
    A node that is shared in between different clips to
    apply the same modification.

    TODO: I'm not sure if I will use this one...
    """

    def __init__(
        self,
        node: TimelineNode,
        cached_output: Union['np.ndarray', 'moderngl.Texture', None]
    ):
        self.node: TimelineNode = node
        """
        The node to execute and to obtain the output from.
        """
        self.cached_output: Union['np.ndarray', 'moderngl.Texture', None] = cached_output
        """
        The output that is cached in this instance to be
        able to access to it from other clips and/or nodes
        in the system.
        """

    def process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        **kwargs
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the input and obtain a result as the output,
        that will be cached in this instance to be able to
        access to it, or returned if it's been previously
        applied.
        """
        if self.cached_output is None:
            # TODO: Is this useful if we only calculate it
            # once (?)
            self.cached_output = self.node.process(
                input = input,
                **kwargs
            )

        return self.cached_output
    
"""
TODO: I don't understand this node, but it was
suggested so maybe it is useful...
"""
# class FloatingNode(TimelineNode):
#     """
#     TODO: A node that I don't understand at all...
#     """
#     def __init__(self, node: TimelineNode, blend_mode="add"):
#         self.node = node
#         self.blend_mode = blend_mode

#     def process(self, input, **kwargs):
#         base = input
#         float_out = self.node.process(input, **kwargs)
#         return self._blend(base, float_out, self.blend_mode)

#     def _blend(self, base, top, mode):
#         if mode == "add":
#             return base + top
#         elif mode == "multiply":
#             return base * top
#         else:
#             return 0.5 * base + 0.5 * top
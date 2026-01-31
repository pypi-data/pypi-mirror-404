from yta_editor_nodes.timeline import TimelineNode
from abc import ABC, abstractmethod
from typing import Union


class _LayerNodeAbstract(TimelineNode, ABC):
    """
    The abstract class of the parallel node.
    """

    def __init__(
        self,
        layers: list[TimelineNode],
        blend_modes: list[str]
    ):
        self.layers: list[TimelineNode] = layers
        """
        The list of layers that will be combined to generate
        a single output.
        """
        self.blend_modes: list[str] = blend_modes
        # TODO: What about the blend mode (?)
        # TODO: Should we make each layer have a blend mode (?)

    def process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        **kwargs
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the input and obtain a result as the output.
        """
        base = self.layers[0].process(
            input = input,
            **kwargs
        )

        for layer, mode in zip(self.layers[1:], self.blend_modes[1:]):
            top = layer.process(
                input = input,
                **kwargs
            )
            base = self._blend(base, top, mode)

        return base
    
    @abstractmethod
    def _blend(
        self,
        base: Union['np.ndarray', 'moderngl.Texture'],
        top: Union['np.ndarray', 'moderngl.Texture'],
        # TODO: What is the mode (?)
        mode = str
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Blend the `base` and `top` inputs provided, using
        the also given `mode`, to obtain an output.
        """
        pass
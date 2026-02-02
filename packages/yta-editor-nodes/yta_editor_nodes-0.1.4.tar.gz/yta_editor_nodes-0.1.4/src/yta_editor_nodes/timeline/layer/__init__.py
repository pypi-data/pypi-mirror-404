from yta_editor_nodes.timeline.layer.abstract import _LayerNodeAbstract
from abc import abstractmethod
from typing import Union


class LayerNode(_LayerNodeAbstract):
    """
    A node that is built by layers whose outputs are
    combined into a single one.

    TODO: I don't really know how this works...

    TODO: This is just a basic class using the MixBlender
    to combine the outputs. We can create more...
    """

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
        # TODO: This must be according to the type
        from yta_editor_nodes.blender import MixBlender

        blender = MixBlender(
            do_use_gpu = True
        )

        return blender.process(
            base_input = base,
            overlay_input = top,
            mix_weight = 1.0
        )
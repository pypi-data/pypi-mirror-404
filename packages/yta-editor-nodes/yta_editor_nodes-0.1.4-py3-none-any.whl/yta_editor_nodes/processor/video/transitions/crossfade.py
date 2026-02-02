from yta_editor_nodes.processor.video.transitions.base import _TransitionProcessor
from typing import Union


class CrossfadeTransitionProcessor(_TransitionProcessor):
    """
    A transition between the frames of 2 videos,
    transforming the first one into the second one.

    Class that is capable of doing some processing on
    an input by using the GPU or the CPU.
    """

    def _instantiate_cpu_and_gpu_processors(
        self,
        opengl_context: Union['moderngl.Context', None]
    ):
        """
        *For internal use only*

        Instantiate the CPU and GPU processors and return 
        them in that order.
        """
        from yta_editor_nodes_gpu.processor.video.transitions.crossfade import CrossfadeTransitionNodeProcessorGPU

        node_cpu = None
        node_gpu = CrossfadeTransitionNodeProcessorGPU(
            opengl_context = opengl_context
        )

        return node_cpu, node_gpu
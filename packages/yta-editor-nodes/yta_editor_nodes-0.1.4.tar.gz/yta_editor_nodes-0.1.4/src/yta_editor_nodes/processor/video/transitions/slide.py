from yta_editor_nodes.processor.video.transitions.base import _TransitionProcessor
from typing import Union


class SlideTransitionProcessor(_TransitionProcessor):
    """
    A transition in which the frames goes from one
    side to the other, disappearing the first one
    and appearing the second one.

    Class that is capable of doing some processing on
    an input by using the GPU or the CPU.
    """

    def _instantiate_cpu_and_gpu_processors(
        self,
        opengl_context: Union['moderngl.Context', None],
    ):
        """
        *For internal use only*

        Instantiate the CPU and GPU processors and return 
        them in that order.
        """
        # TODO: Maybe rename to 'SlideTransitionNodeProcessorGPU' (?)
        from yta_editor_nodes_cpu.processor.video.transitions.slide import SlideTransitionProcessorCPU
        from yta_editor_nodes_gpu.processor.video.transitions.slide import SlideTransitionNodeProcessorGPU

        node_cpu = SlideTransitionProcessorCPU()
        node_gpu = SlideTransitionNodeProcessorGPU(
            opengl_context = opengl_context
        )

        return node_cpu, node_gpu
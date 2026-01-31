from yta_editor_nodes.processor.video.transitions.base import _TransitionProcessor
from typing import Union


class CircleClosingTransitionProcessor(_TransitionProcessor):
    """
    A transition between the frames of 2 videos in
    which the frames are mixed by generating a circle
    that decreases its size from the whole screen
    until disappearing.

    Class that is capable of doing some processing on
    an input by using the GPU or the CPU.
    """

    def __init__(
        self,
        opengl_context: Union['moderngl.Context', None]
    ):
        super().__init__(
            opengl_context = opengl_context
        )

    def _instantiate_cpu_and_gpu_processors(
        self,
        opengl_context: Union['moderngl.Context', None]
    ):
        """
        *For internal use only*

        Instantiate the CPU and GPU processors and return 
        them in that order.
        """
        from yta_editor_nodes_gpu.processor.video.transitions.circle_closing import CircleClosingTransitionNodeProcessorGPU

        node_cpu = None
        node_gpu = CircleClosingTransitionNodeProcessorGPU(
            opengl_context = opengl_context
        )

        return node_cpu, node_gpu
    
    def process(
        self,
        first_input: Union['moderngl.Texture', 'np.ndarray'],
        second_input: Union['moderngl.Texture', 'np.ndarray'],
        progress: float,
        output_size: Union[tuple[int, int], None],
        do_use_gpu: bool = True,
        border_smoothness: float = 0.02
    ) -> Union['moderngl.Texture', 'np.ndarray']:
        return super().process(
            first_input = first_input,
            second_input = second_input,
            progress = progress,
            output_size = output_size,
            do_use_gpu = do_use_gpu,
            border_smoothness = border_smoothness
        )
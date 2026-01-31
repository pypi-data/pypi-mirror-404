from yta_editor_nodes.processor.video.transitions.base import _TransitionProcessor
from typing import Union


class DistortedCrossfadeTransitionProcessor(_TransitionProcessor):
    """
    A transition between the frames of 2 videos,
    transforming the first one into the second one
    with a distortion in between.

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
        from yta_editor_nodes_gpu.processor.video.transitions.distorted_crossfade import DistortedCrossfadeTransitionNodeProcessorGPU

        node_cpu = None
        node_gpu = DistortedCrossfadeTransitionNodeProcessorGPU(
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
        intensity: float = 1.0
    ) -> Union['moderngl.Texture', 'np.ndarray']:
        return super().process(
            first_input = first_input,
            second_input = second_input,
            progress = progress,
            output_size = output_size,
            do_use_gpu = do_use_gpu,
            intensity = intensity
        )
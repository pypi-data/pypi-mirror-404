from yta_editor_nodes.processor.video.transitions.base import _TransitionProcessor
from typing import Union


class BarsFallingTransitionProcessor(_TransitionProcessor):
    """
    A transition between the frames of 2 videos in which
    a set of bars fall with the first video to let the
    second one be seen.

    Class that is capable of doing some processing on
    an input by using the GPU or the CPU.
    """

    def __init__(
        self,
        opengl_context: Union['moderngl.Context', None]
    ):
        super().__init__(
            opengl_context
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
        from yta_editor_nodes_gpu.processor.video.transitions.bars_falling import BarsFallingTransitionNodeProcessorGPU

        node_cpu = None
        node_gpu = BarsFallingTransitionNodeProcessorGPU(
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
        number_of_bars: int = 30,
        amplitude: float = 2.0,
        noise: float = 0.1,
        frequency: float = 0.5,
        drip_scale: float = 0.5
    ) -> Union['moderngl.Texture', 'np.ndarray']:
        return super().process(
            first_input = first_input,
            second_input = second_input,
            progress = progress,
            output_size = output_size,
            do_use_gpu = do_use_gpu,
            number_of_bars = number_of_bars,
            amplitude = amplitude,
            noise = noise,
            frequency = frequency,
            drip_scale = drip_scale
        )
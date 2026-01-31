from yta_editor_nodes.processor.video.base import _VideoNodeProcessor
from typing import Union


class WavingFrameVideoNodeProcessor(_VideoNodeProcessor):
    """
    The frame but as if it is moving like a wave.
    """

    def __init__(
        self,
        opengl_context: 'moderngl.Context'
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

        Instantiate the CPU and GPU procesors and return 
        them in that order.

        This method must be implemented by each class.
        """
        from yta_editor_nodes_cpu.processor.video.waving_frame import WavingFrameVideoNodeProcessorCPU
        from yta_editor_nodes_gpu.processor.video.waving_frame import WavingFrameVideoNodeProcessorGPU

        node_cpu = WavingFrameVideoNodeProcessorCPU()
        node_gpu = WavingFrameVideoNodeProcessorGPU(
            opengl_context = opengl_context
        )

        return node_cpu, node_gpu
    
    def process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        output_size: Union[tuple[int, int], None],
        do_use_gpu: bool = True,
        t: float = 0.0,
        amplitude: float = 0.05,
        frequency: float = 10.0,
        speed: float = 2.0,
        do_use_transparent_pixels: bool = False
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided 'input' with GPU or CPU 
        according to the internal flag.
        """
        return super().process(
            input = input,
            output_size = output_size,
            do_use_gpu = do_use_gpu,
            t = t,
            amplitude = amplitude,
            frequency = frequency,
            speed = speed,
            do_use_transparent_pixels = do_use_transparent_pixels
        )
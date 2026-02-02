from yta_editor_nodes.processor.base import _NodeProcessor
from yta_editor_nodes.utils import get_input_size
from typing import Union


class BlackAndWhiteNodeProcessor(_NodeProcessor):
    """
    The node to modify the input provided and set
    it as black and white by using CPU or GPU.
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

        Instantiate the CPU and GPU procesors and return 
        them in that order.

        This method must be implemented by each class.
        """
        from yta_editor_nodes_cpu.processor.black_and_white import BlackAndWhiteNodeProcessorCPU
        from yta_editor_nodes_gpu.processor.black_and_white import BlackAndWhiteNodeProcessorGPU

        node_cpu = BlackAndWhiteNodeProcessorCPU()
        node_gpu = BlackAndWhiteNodeProcessorGPU(
            opengl_context = opengl_context
        )

        return node_cpu, node_gpu

    def process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        # This is to accept 't' even when unneeded
        **kwargs
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided `input` with GPU or CPU 
        according to the internal flag.
        """
        output_size = (
            get_input_size(input)
            if output_size is None else
            output_size
        )

        processor = self._get_processor(
            do_use_gpu = do_use_gpu
        )

        return processor.process(
            input = self._prepare_input(
                input = input,
                do_use_gpu = do_use_gpu
            ),
            output_size = output_size,
        )
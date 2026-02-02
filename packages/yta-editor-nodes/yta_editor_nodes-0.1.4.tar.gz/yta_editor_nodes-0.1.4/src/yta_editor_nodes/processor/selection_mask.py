from yta_editor_nodes.processor.base import _NodeProcessor
from yta_editor_nodes.utils import get_input_size
from typing import Union


class SelectionMaskNodeProcessor(_NodeProcessor):
    """
    Class to use a mask selection (from which we will
    determine if the pixel must be applied or not) to
    apply the processed input over the original one.

    If the selection mask is completely full, the
    result will be the processed input.
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
        from yta_editor_nodes_cpu.processor.selection_mask import SelectionMaskNodeProcessorCPU
        from yta_editor_nodes_gpu.processor.selection_mask import SelectionMaskNodeProcessorGPU

        node_cpu = SelectionMaskNodeProcessorCPU()
        node_gpu = SelectionMaskNodeProcessorGPU(
            opengl_context = opengl_context
        )

        return node_cpu, node_gpu

    def process(
        self,
        original_input: Union['np.ndarray', 'moderngl.Texture'],
        processed_input: Union['np.ndarray', 'moderngl.Texture'],
        selection_mask_input: Union['np.ndarray', 'moderngl.Texture'],
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided inputs with GPU or CPU 
        according to the internal flag.
        """
        output_size = (
            get_input_size(original_input)
            if output_size is None else
            output_size
        )

        processor = self._get_processor(
            do_use_gpu = do_use_gpu
        )

        return processor.process(
            original_input = self._prepare_input(
                input = original_input,
                do_use_gpu = do_use_gpu
            ),
            processed_input = self._prepare_input(
                input = processed_input,
                do_use_gpu = do_use_gpu
            ),
            selection_mask_input = self._prepare_input(
                input = selection_mask_input,
                do_use_gpu = do_use_gpu
            ),
            output_size = output_size,
        )
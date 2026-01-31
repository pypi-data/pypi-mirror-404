from yta_editor_nodes.processor.base import _ProcessorGPUAndCPU
from yta_editor_nodes.utils import get_input_size
from typing import Union
from abc import abstractmethod


class _NodeCompositor(_ProcessorGPUAndCPU):
    """
    *For internal use only*

    This class must be inherited by the specific
    implementation of some node that will be positioning
    inputs, done by CPU or GPU (at least one of the
    options)

    A node specifically designed to build a scene by
    positioning inputs in different positions and 
    obtaining a single output by using GPU or CPU.
    """

    def __init__(
        self,
        opengl_context: Union['moderngl.Context', None],
        **kwargs
    ):
        node_compositor_cpu, node_compositor_gpu = self._instantiate_cpu_and_gpu_processors(
            opengl_context = opengl_context,
            **kwargs
        )

        super().__init__(
            processor_cpu = node_compositor_cpu,
            processor_gpu = node_compositor_gpu,
            opengl_context = opengl_context
        )

    @abstractmethod
    def _instantiate_cpu_and_gpu_processors(
        self,
        opengl_context: Union['moderngl.Context', None],
        **kwargs
    ):
        """
        *For internal use only*

        Instantiate the CPU and GPU procesors and return 
        them in that order.

        This method must be implemented by each class.
        """
        pass

    # TODO: Maybe @abstractmethod cause' they are different
    def process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        **kwargs
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided `input` with GPU or CPU 
        according to the `do_use_gpu` flag provided.
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
            **kwargs
        )
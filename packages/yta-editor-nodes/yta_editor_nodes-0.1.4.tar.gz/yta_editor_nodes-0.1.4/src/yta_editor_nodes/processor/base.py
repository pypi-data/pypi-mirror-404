from yta_editor_nodes.abstract import _ProcessorGPUAndCPU
from typing import Union
from abc import abstractmethod, ABC


class _NodeProcessor(_ProcessorGPUAndCPU, ABC):
    """
    *For internal use only*

    *Singleton class*

    This class must be inherited by the specific
    implementation of some effect that will be done by
    CPU or GPU (at least one of the options)

    A simple processor node that is capable of
    processing inputs and obtain a single output by
    using the GPU or the CPU.

    This type of node is for the effects and 
    transitions.
    """

    def __init__(
        self,
        opengl_context: Union['moderngl.Context', None],
        **kwargs
    ):
        """
        The `opengl_context` will be passed to the GPU node
        if needed (and existing).
        """
        node_complex_cpu, node_complex_gpu = self._instantiate_cpu_and_gpu_processors(
            opengl_context = opengl_context,
            **kwargs
        )

        super().__init__(
            processor_cpu = node_complex_cpu,
            processor_gpu = node_complex_gpu,
            opengl_context = opengl_context
        )

    @abstractmethod
    def _instantiate_cpu_and_gpu_processors(
        self,
        opengl_context: Union['moderngl.Context', None]
    ):
        """
        *For internal use only*

        Instantiate the CPU and GPU procesors and return 
        them in that order.

        This method must be implemented in each class.
        """
        pass

    def _process_common(
        self,
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        **kwargs
    ):
        processor = self._get_processor(
            do_use_gpu = do_use_gpu
        )

        # The inputs must be transformed before reaching
        # this point

        # The **kwargs here will include inputs and other
        # parameters defined in the specific children

        return processor.process(
            output_size = output_size,
            **kwargs
        )
from yta_editor_nodes.processor.base import _ProcessorGPUAndCPU
from typing import Union
from abc import abstractmethod


class _NodeComplex(_ProcessorGPUAndCPU):
    """
    *For internal use only*

    This class must be inherited by the specific
    implementation of some complex node that will be
    done by CPU or GPU (at least one of the options)

    A complex node, which is a node made by other nodes,
    that is capable of processing inputs and obtain a
    single output by using the GPU or the CPU.

    This type of node is for complex modifications.
    """

    def __init__(
        self,
        opengl_context: Union['moderngl.Context', None],
        **kwargs
    ):
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

    # @abstractmethod
    # def process(
    #     self,
    #     input: Union['np.ndarray', 'moderngl.Texture'],
    #     output_size: Union[tuple[int, int], None] = None,
    #     do_use_gpu: bool = True,
    #     **kwargs
    # ) -> Union['np.ndarray', 'moderngl.Texture']:
    #     """
    #     Process the provided 'input' with GPU or CPU 
    #     according to the internal flag.
    #     """
    #     pass
        
    def _process_common(
        self,
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        **kwargs
    ):
        processor = self._get_processor(
            do_use_gpu = do_use_gpu
        )

        # TODO: Transform the inputs if needed, based on
        # the type and the processor we got: numpy to
        # texture if GPU, texture to numpy if CPU

        # The **kwargs here will include inputs and other
        # parameters defined in the specific children
        return processor.process(
            output_size = output_size,
            **kwargs
        )
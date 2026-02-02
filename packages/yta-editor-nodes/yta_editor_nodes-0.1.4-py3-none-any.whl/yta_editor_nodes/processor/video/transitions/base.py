from yta_editor_nodes.processor.base import _ProcessorGPUAndCPU
from yta_editor_nodes.utils import get_input_size
from typing import Union
from abc import abstractmethod


class _TransitionProcessor(_ProcessorGPUAndCPU):
    """
    *Abstract class*
    
    *Singleton class*

    *For internal use only*

    *This class must be inherited by the specific
    implementation of some transition that will be
    done by CPU or GPU (at least one of the options)*

    Class that is capable of doing some processing on
    an input by using the GPU or the CPU.
    """

    def __init__(
        self,
        opengl_context: Union['moderngl.Context', None],
        **kwargs
    ):
        """
        The `do_use_gpu` boolean flag will be set by the
        user when instantiating the class to choose between
        GPU and CPU to process the input.
        """
        transition_processor_cpu, transition_processor_gpu = self._instantiate_cpu_and_gpu_processors(
            opengl_context = opengl_context,
            **kwargs
        )

        super().__init__(
            processor_cpu = transition_processor_cpu,
            processor_gpu = transition_processor_gpu,
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

        Instantiate the CPU and GPU processors and return 
        them in that order.

        This method must be implemented by each class.
        """
        pass

    def process(
        self,
        first_input: Union['moderngl.Texture', 'np.ndarray'],
        second_input: Union['moderngl.Texture', 'np.ndarray'],
        progress: float,
        output_size: Union[tuple[int, int], None],
        do_use_gpu: bool = True,
        **kwargs
    ) -> Union['moderngl.Texture', 'np.ndarray']:
        """
        Process the transition between the given `first_input`
        and `second_input` depending on the `progress`
        provided, with GPU or CPU according to the `do_use_gpu`
        value.
        """
        output_size = (
            get_input_size(first_input)
            if output_size is None else
            output_size
        )

        processor = self._get_processor(
            do_use_gpu = do_use_gpu
        )

        return processor.process(
            first_input = self._prepare_input(
                input = first_input,
                do_use_gpu = do_use_gpu
            ),
            second_input = self._prepare_input(
                input = second_input,
                do_use_gpu = do_use_gpu
            ),
            progress = progress,
            output_size = output_size,
            **kwargs
        )
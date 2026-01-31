from yta_editor_nodes.processor.base import _ProcessorGPUAndCPU
from yta_editor_nodes.utils import get_input_size
from typing import Union
from abc import abstractmethod


class _Blender(_ProcessorGPUAndCPU):
    """
    *For internal use only*

    This class must be inherited by the specific
    implementation of some blenders that will use
    CPU or GPU (at least one of the options).

    Class that is capable of mixing 2 different
    inputs by using the GPU or the CPU.
    """

    def __init__(
        self,
        opengl_context: Union['moderngl.Context', None] = None,
        **kwargs
    ):
        """
        The `do_use_gpu` boolean flag will be set by the
        user when instantiating the class to choose between
        GPU and CPU to process the input.
        """
        blender_cpu, blender_gpu = self._instantiate_cpu_and_gpu_blenders(
            opengl_context = opengl_context,
            **kwargs
        )

        super().__init__(
            processor_cpu = blender_cpu,
            processor_gpu = blender_gpu,
            opengl_context = opengl_context
        )

    @abstractmethod
    def _instantiate_cpu_and_gpu_blenders(
        self,
        opengl_context: Union['moderngl.Context', None],
        **kwargs
    ):
        """
        *For internal use only*

        Instantiate the CPU and GPU blenders and return 
        them in that order.

        This method must be implemented by each class.
        """
        pass

    def process(
        self,
        base_input: Union['np.ndarray', 'moderngl.Texture'],
        overlay_input: Union['np.ndarray', 'moderngl.Texture'],
        # TODO: Maybe set it automatically based on the texture
        # size (?)
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        mix_weight: float = 1.0,
        **kwargs
    # TODO: What about the output type (?)
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided 'base_input' and 'overlay_input'
        with GPU or CPU according to the internal flag.

        The `mix_weight` will determine how much of the result
        we keep against the base, where a `mix_weight == 1.0`
        means that we want the result at 100%, but a
        `mix_weight == 0.4` means a 40% of the result and a 60%
        of the base.
        """
        output_size = (
            get_input_size(base_input)
            if output_size is None else
            output_size
        )

        processor = self._get_processor(
            do_use_gpu = do_use_gpu
        )

        # TODO: Transform the inputs if needed, based on
        # the type and the processor we got: numpy to
        # texture if GPU, texture to numpy if CPU

        return processor.process(
            base_input = self._prepare_input(
                input = base_input,
                do_use_gpu = do_use_gpu
            ),
            overlay_input = self._prepare_input(
                input = overlay_input,
                do_use_gpu = do_use_gpu
            ),
            output_size = output_size,
            mix_weight = mix_weight,
            **kwargs
        )
    
    def blend_multiple_inputs(
        self,
        inputs: list[Union['np.ndarray', 'moderngl.Texture']],
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        mix_weights: Union[list[float], float] = 1.0,
        **kwargs
    # TODO: What about the output type (?)
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided 'inputs' with GPU or CPU
        according to the internal flag.
        """
        # TODO: What do we do with the 'output_size' (?)
        output_size = (
            get_input_size(inputs[0])
            if output_size is None else
            output_size
        )

        processor = self._get_processor(
            do_use_gpu = do_use_gpu
        )

        # TODO: Transform the inputs if needed, based on
        # the type and the processor we got: numpy to
        # texture if GPU, texture to numpy if CPU

        return processor.process_multiple_inputs(
            inputs = inputs,
            output_size = output_size,
            mix_weights = mix_weights,
            **kwargs
        )
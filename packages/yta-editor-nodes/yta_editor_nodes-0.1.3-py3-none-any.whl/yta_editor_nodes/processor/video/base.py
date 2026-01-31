from yta_editor_nodes.processor.base import _NodeProcessor
from yta_editor_nodes.utils import get_input_size
from typing import Union
from abc import ABC


# TODO: ABC, do we need it (?)
class _VideoNodeProcessor(_NodeProcessor, ABC):
    """
    *For internal use only*
    
    *Abstract class*

    This class must be inherited by the specific
    implementation of some effect that will be done by
    CPU or GPU (at least one of the options).

    Class that is capable of doing some processing on
    an input by using the GPU or the CPU, but for 
    video frames, including a `t` time moment parameter
    when processing.
    """

    def process(
        self,
        input: Union['np.ndarray', 'moderngl.Texture'],
        output_size: Union[tuple[int, int], None],
        do_use_gpu: bool = True,
        t: float = 0.0,
        **kwargs
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided 'input' with GPU or CPU 
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
            t = t,
            **kwargs
        )
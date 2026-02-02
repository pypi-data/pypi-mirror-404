from yta_editor_nodes.processor.video.transitions.base import _TransitionProcessor
from yta_editor_nodes.utils import get_input_size
from typing import Union


class AlphaPediaMaskTransitionProcessor(_TransitionProcessor):
    """
    A transition made by using a custom mask to
    join the 2 videos. This mask is specifically
    obtained from the AlphaPediaYT channel in which
    we upload specific masking videos.

    Both videos will be placed occupying the whole
    scene, just overlapping by using the transition
    video mask, but not moving the frame through 
    the screen like other classes do (like the
    FallingBars).

    Class that is capable of doing some processing on
    an input by using the GPU or the CPU.
    """

    def _instantiate_cpu_and_gpu_processors(
        self,
        opengl_context: Union['moderngl.Context', None]
    ):
        """
        *For internal use only*

        Instantiate the CPU and GPU processors and return 
        them in that order.
        """
        from yta_editor_nodes_gpu.processor.video.transitions.alphapedia_mask import AlphaPediaMaskTransitionNodeProcessorGPU

        node_cpu = None
        node_gpu = AlphaPediaMaskTransitionNodeProcessorGPU(
            opengl_context = opengl_context,
        )

        return node_cpu, node_gpu
    
    def process(
        self,
        first_input: Union['moderngl.Texture', 'np.ndarray'],
        second_input: Union['moderngl.Texture', 'np.ndarray'],
        mask_input: Union['moderngl.Texture', 'np.ndarray'],
        progress: float,
        output_size: Union[tuple[int, int], None],
        do_use_gpu: bool = True
    ) -> Union['moderngl.Texture', 'np.ndarray']:
        """
        Process the transition between the given `first_input`
        and `second_input`, with GPU or CPU according to the
        internal flag.
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
            mask_input = self._prepare_input(
                input = mask_input,
                do_use_gpu = do_use_gpu
            ),
            progress = progress,
        )
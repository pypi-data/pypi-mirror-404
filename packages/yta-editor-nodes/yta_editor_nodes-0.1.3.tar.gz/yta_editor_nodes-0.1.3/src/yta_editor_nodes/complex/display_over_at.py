from yta_editor_nodes.complex.base import _NodeComplex
from yta_editor_nodes.utils import get_input_size
from typing import Union


class DisplayOverAtNodeComplex(_NodeComplex):
    """
    The overlay input is positioned with the given position,
    rotation and size, and then put as an overlay of the
    also given base input.

    Information:
    - The scene size is `(1920, 1080)`, so provide the
    `position` parameter according to it, where it is
    representing the center of the texture.
    - The `rotation` is in degrees, where `rotation=90`
    means rotating 90 degrees to the right.
    - The `size` parameter must be provided according to
    the previously mentioned scene size `(1920, 1080)`.

    TODO: This has no inheritance, is special and we need
    to be able to identify it as a valid one.
    """

    def _instantiate_cpu_and_gpu_processors(
        self,
        opengl_context: Union['moderngl.Context', None]
    ):
        """
        *For internal use only*

        Instantiate the CPU and GPU blenders and return 
        them in that order.

        This method must be implemented by each class.
        """
        from yta_editor_nodes_cpu.complex.display_over_at import DisplayOverAtNodeComplexCPU
        from yta_editor_nodes_gpu.complex.display_over_at import DisplayOverAtNodeComplexGPU

        node_cpu = DisplayOverAtNodeComplexCPU()
        node_gpu = DisplayOverAtNodeComplexGPU(
            opengl_context = opengl_context
        )

        return node_cpu, node_gpu
    
    def process(
        self,
        base_input: Union['np.ndarray', 'moderngl.Texture'],
        overlay_input: Union['np.ndarray', 'moderngl.Texture'],
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        position: tuple[int, int] = (1920 / 2, 1080 / 2),
        size: tuple[int, int] = (1920 / 2, 1080 / 2),
        rotation: int = 0
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Put the `overlapy_input` over the `base_input` in
        the `position` given and with the `size` and
        `rotation` also provided.
        """
        output_size = (
            get_input_size(base_input)
            if output_size is None else
            output_size
        )

        processor = self._get_processor(
            do_use_gpu = do_use_gpu
        )

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
            position = position,
            size = size,
            rotation = rotation
        )
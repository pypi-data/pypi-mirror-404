from yta_editor_nodes.compositor.base import _NodeCompositor
from yta_editor_nodes.utils import get_input_size
from typing import Union


class DisplacementWithRotationNodeCompositor(_NodeCompositor):
    """
    The frame, but moving and rotating over other frame.
    """

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
        from yta_editor_nodes_cpu.compositor.displacement_with_rotation import DisplacementWithRotationNodeCompositorCPU
        from yta_editor_nodes_gpu.compositor.displacement_with_rotation import DisplacementWithRotationNodeCompositorGPU

        node_cpu = DisplacementWithRotationNodeCompositorCPU()
        node_gpu = DisplacementWithRotationNodeCompositorGPU(
            opengl_context = opengl_context
        )

        return node_cpu, node_gpu
    
    def process(
        self,
        base_input: Union['np.ndarray', 'moderngl.Texture'],
        overlay_input: Union['np.ndarray', 'moderngl.Texture'],
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        position: tuple[int, int] = (1920 / 2 * 1.5, 1080 / 2 * 1.5),
        size: tuple[int, int] = (1920 / 2 * 1.5, 1080 / 2 * 1.5),
        rotation: int = 45
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided 'input' with GPU or CPU 
        according to the internal flag.
        """
        input_for_size = (
            base_input
            if base_input is not None else
            overlay_input
        )

        output_size = (
            get_input_size(input_for_size)
            if output_size is None else
            output_size
        )

        processor = self._get_processor(
            do_use_gpu = do_use_gpu
        )

        base_input = (
            self._prepare_input(
                input = base_input,
                do_use_gpu = do_use_gpu
            )
            if base_input is not None else
            None
        )

        return processor.process(
            base_input = base_input,
            overlay_input = self._prepare_input(
                input = overlay_input,
                do_use_gpu = do_use_gpu
            ),
            output_size = output_size,
            position = position,
            size = size,
            rotation = rotation
        )
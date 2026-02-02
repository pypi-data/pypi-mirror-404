from yta_editor_nodes.blender.base import _Blender
from typing import Union


class MixBlender(_Blender):
    """
    A blender that uses a float value to mix the
    result with the original input as much as that
    value determines.
    """

    def __init__(
        self,
        opengl_context: Union['moderngl.Context', None]
    ):
        super().__init__(
            opengl_context = opengl_context
        )

    def _instantiate_cpu_and_gpu_blenders(
        self,
        opengl_context: Union['moderngl.Context', None]
    ):
        """
        *For internal use only*

        Instantiate the CPU and GPU blenders and return 
        them in that order.

        This method has been created to be used in both the
        '__init__' and the '__reinit__' methods.

        This method must be implemented by each class.
        """
        from yta_editor_nodes_cpu.blender.mix import MixBlenderCPU
        from yta_editor_nodes_gpu.blender.mix import MixBlenderGPU

        node_cpu = MixBlenderCPU()
        node_gpu = MixBlenderGPU(
            opengl_context = opengl_context
        )

        return node_cpu, node_gpu

    def blend(
        self,
        base_input: Union['np.ndarray', 'moderngl.Texture'],
        overlay_input: Union['np.ndarray', 'moderngl.Texture'],
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        mix_weight: float = 1.0
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
        return self.process(
            base_input = base_input,
            overlay_input = overlay_input,
            output_size = output_size,
            do_use_gpu = do_use_gpu,
            mix_weight = mix_weight
        )
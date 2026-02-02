from yta_editor_nodes.blender.base import _Blender
from typing import Union


class AlphaBlender(_Blender):
    """
    The most common blender used in video edition.

    This blender will use the alpha channel of the 
    overlay input, multiplied by the `blend_strength`
    parameter provided, to use it as the mixer factor
    between the base and the overlay inputs.
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
        from yta_editor_nodes_cpu.blender.alpha import AlphaBlenderCPU
        from yta_editor_nodes_gpu.blender.alpha import AlphaBlenderGPU

        node_cpu = AlphaBlenderCPU()
        node_gpu = AlphaBlenderGPU(
            opengl_context = opengl_context
        )

        return node_cpu, node_gpu

    def blend(
        self,
        base_input: Union['np.ndarray', 'moderngl.Texture'],
        overlay_input: Union['np.ndarray', 'moderngl.Texture'],
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        mix_weight: float = 1.0,
        blend_strength: float = 1.0
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
        return self.process(
            base_input = base_input,
            overlay_input = overlay_input,
            output_size = output_size,
            do_use_gpu = do_use_gpu,
            mix_weight = mix_weight,
            blend_strength = blend_strength
        )
    
    # TODO: This method has to be reviewed in the general
    # class to be able to receive array parameters and
    # send them to the individual process as single parameter
    def blend_multiple_inputs(
        self,
        inputs: list[Union['np.ndarray', 'moderngl.Texture']],
        output_size: Union[tuple[int, int], None] = None,
        do_use_gpu: bool = True,
        mix_weights: Union[list[float], float] = 1.0,
        blend_strengths: Union[list[float], float] = 1.0,
    # TODO: What about the output type (?)
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided 'inputs' with GPU or CPU
        according to the internal flag.
        """
        return self.blend_multiple_inputs(
            inputs = inputs,
            output_size = output_size,
            do_use_gpu = do_use_gpu,
            mix_weights = mix_weights,
            blend_strengths = blend_strengths
        )
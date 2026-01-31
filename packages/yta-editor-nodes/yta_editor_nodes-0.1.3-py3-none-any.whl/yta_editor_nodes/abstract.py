from yta_video_opengl.context import OpenGLContext
from yta_validation import PythonValidator
from yta_editor_utils.texture import TextureUtils
from abc import abstractmethod
from typing import Union


class _ProcessorGPUAndCPU:
    """
    *For internal use only*

    *Abstract class*

    Abstract class to share the common behaviour of
    being able to handle a process with a GPU and/or
    a CPU processor, chosen by the user.
    """

    @property
    def is_gpu_available(
        self
    ) -> bool:
        """
        Boolean flag to indicate if the GPU is available
        or not, that means that the processor that uses
        GPU is set.
        """
        return self._processor_gpu is not None
    
    @property
    def is_cpu_available(
        self
    ) -> bool:
        """
        Boolean flag to indicate if the CPU is available
        or not, that means that the processor that uses
        CPU is set.
        """
        return self._processor_cpu is not None
    
    def __init__(
        self,
        processor_cpu: Union['_ProcessorGPU', None] = None,
        processor_gpu: Union['_ProcessorCPU', None] = None,
        opengl_context: Union['moderngl.Context', None] = None,
    ):
        """
        The `processor_cpu` and `processor_gpu` have to be
        set by the developer when building the specific
        classes, but the `do_use_gpu` boolean flag will be
        set by the user when instantiating the class to
        choose between GPU and CPU.

        The `opengl_context` is needed to instantiate the
        GPU unit but also to transform the input into a
        `moderngl.Texture` if needed.
        """
        if (
            processor_cpu is None and
            processor_gpu is None
        ):
            raise Exception('No node processor provided. At least one node processor is needed.')

        self._processor_cpu: Union['_ProcessorCPU', None] = processor_cpu
        """
        *For internal use only*

        The transition processor that is able to do the
        processing by using the CPU. If it is None we cannot
        process it with CPU.
        """
        self._processor_gpu: Union['_ProcessorGPU', None] = processor_gpu
        """
        *For internal use only*

        The transition processor that is able to do the
        processing by using the GPU. If it is None we cannot
        process it with GPU.
        """
        self._opengl_context: Union['moderngl.Context', None] = (
            OpenGLContext().context
            if opengl_context is None else
            opengl_context
        )
        """
        *For internal use only*

        The context that we will use for the GPU node.
        """

    def _get_processor(
        self,
        do_use_gpu: bool
    ) -> Union['ProcessorGPU', 'ProcessorCPU']:
        """
        *For internal use only*

        Get the processor according to the `do_use_gpu`
        parameter provided and if the one requested is
        available or not.
        """
        return (
            (
                # Prefer GPU if available
                self._processor_gpu or
                self._processor_cpu
            ) if do_use_gpu else (
                # Prefer CPU if available
                self._processor_cpu or
                self._processor_gpu
            )
        )
    
    # TODO: Maybe move to a more general thing (?)
    def _prepare_input(
        self,
        input: Union['moderngl.Texture', 'np.ndarray'],
        do_use_gpu: bool
    ) -> Union['moderngl.Texture', 'np.ndarray']:
        """
        *For internal use only*

        Prepare the `input` provided based on the `do_use_gpu`
        parameter given to be used with the processer,
        according to the availability.

        This method will transform a `texture` into a `numpy`
        array if they are asking for CPU and it is available,
        or a `numpy` into a `texture` if they are asking for
        GPU and it is available.
        """
        # 1. Get the backend we need
        if do_use_gpu and self.is_gpu_available:
            backend = 'gpu'
        elif not do_use_gpu and self.is_cpu_available:
            backend = 'cpu'
        elif self.is_gpu_available:
            backend = 'gpu'
        elif self.is_cpu_available:
            backend = 'cpu'
        else:
            raise RuntimeError("Node has neither CPU nor GPU implementation")

        return (
            # Is texture but ask CPU and available
            TextureUtils.texture_to_numpy(
                texture = input,
                do_include_alpha = True
            )
            if (
                backend == 'cpu' and
                not PythonValidator.is_numpy_array(input)
            ) else
            # Is numpy but ask GPU and available
            TextureUtils.numpy_to_texture(
                input = input,
                opengl_context = self._opengl_context
            )
            if (
                backend == 'gpu' and
                PythonValidator.is_numpy_array(input)
            ) else
            input
        )

        return (
            # Is texture but ask CPU and available
            TextureUtils.texture_to_numpy(
                texture = input,
                do_include_alpha = True
            )
            if (
                self.is_cpu_available and
                not do_use_gpu and
                not PythonValidator.is_numpy_array(input)
            ) else
            # Is numpy but ask GPU and available
            TextureUtils.numpy_to_texture(
                input = input,
                opengl_context = self._opengl_context
            )
            if (
                self.is_gpu_available and
                do_use_gpu and
                PythonValidator.is_numpy_array(input)
            ) else
            input
        )

    @abstractmethod
    def process(
        self,
        input: Union['moderngl.Texture', 'np.ndarray'],
        do_use_gpu: bool = True
    ) -> Union['moderngl.Texture', 'np.ndarray']:
        """
        Process the provided `input` with GPU or CPU 
        according to the internal flag.
        """
        pass
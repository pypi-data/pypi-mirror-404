from typing import Union


# TODO: I think this method is repeated somewhere else...
def get_input_size(
    input: Union['moderngl.Texture', 'np.ndarray']
) -> tuple[int, int]:
    """
    Get the size of the `input` provided, that can be
    a `moderngl.Texture` or a `numpy.ndarray`.

    Supported types:
    - moderngl.Texture
    - numpy.ndarray (H×W or H×W×C)
    """
    from yta_validation import PythonValidator

    if PythonValidator.is_instance_of(input, 'Texture'):
        return (input.width, input.height)
    elif PythonValidator.is_numpy_array(input):
        if input.ndim == 2:
            # Grayscale image: H × W
            height, width = input.shape

            return (width, height)

        if input.ndim == 3:
            # Color image: H × W × C
            height, width, _ = input.shape

            return (width, height)

        raise ValueError(
            f"Unsupported numpy array shape: {input.shape}. "
            "Expected 2D (H×W) or 3D (H×W×C)."
        )
    else:
        raise Exception(f'Unexpected input: {type(input)}')
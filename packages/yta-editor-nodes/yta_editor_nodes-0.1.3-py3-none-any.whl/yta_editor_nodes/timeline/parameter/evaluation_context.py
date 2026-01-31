from typing import Any


class EvaluationContext:
    """
    The circunstances and attributes we need to be
    able to calculate the value of a parameter in
    this specific context.
    """

    def __init__(
        self,
        t: float,
        frame_index: int,
        node_outputs: dict[str, Any],
        curves: dict[str, Any],
        backend: str,
    ):
        self.t = t
        self.frame_index = frame_index
        self.node_outputs = node_outputs
        self.curves = curves
        self.backend = backend
        
    """
    INTERESTING VALUES:
    Tiempo
    Frame index
    FPS
    Resolución
    Seed
    Flags de ejecución
    Cualquier metadata futura
    """

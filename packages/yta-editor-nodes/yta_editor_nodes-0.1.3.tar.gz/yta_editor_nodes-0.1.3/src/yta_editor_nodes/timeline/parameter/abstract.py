from yta_editor_nodes.timeline.parameter.evaluation_context import EvaluationContext
from abc import ABC, abstractmethod
from typing import Any


class ParameterSource(ABC):
    """
    The source that allows us to calculate the
    value of a parameter, based on its context,
    for a specific `t` time moment (wich is
    included in the context).
    """

    @abstractmethod
    def evaluate(
        self,
        context: EvaluationContext
    ) -> Any:
        """
        Evaluate the value for this parameter based on the
        given `context`.
        """
        pass

from yta_editor_nodes.timeline.parameter.evaluation_context import EvaluationContext
from yta_editor_nodes.timeline.parameter.abstract import ParameterSource
from yta_validation.parameter import ParameterValidator
from typing import Union


# TODO: Move from here maybe
BASIC_NON_ITERABLE_TYPE = Union[int, float, bool, str]
"""
The basic non iterable type we can accept as
a parameter and that will be transformed into
a `ConstantValue`, including:
- `int`
- `float`
- `bool`
- `str`

This type has been created for the `ParameterSource`
class.
"""

class ConstantValue(ParameterSource):
    """
    The parameter source in which the value is always
    the same. It is constant, so the context doesn't
    affect it.
    """

    def __init__(
        self,
        value: BASIC_NON_ITERABLE_TYPE
    ):
        ParameterValidator.validate_basic_non_iterable_type('value', value)

        self.value: BASIC_NON_ITERABLE_TYPE = value
        """
        The constant value itself.
        """

    def evaluate(
        self,
        context: EvaluationContext
    ) -> BASIC_NON_ITERABLE_TYPE:
        """
        Get the value for the `context` provided. In this
        case the context will not make any change.
        """
        return self.value
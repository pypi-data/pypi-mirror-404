from yta_editor_nodes.timeline.parameter.evaluation_context import EvaluationContext
from yta_editor_nodes.timeline.parameter.abstract import ParameterSource
from yta_math_easings.abstract import EasingFunctionName
from yta_math_easings.animated.abstract import EasingAnimatedFunction
from typing import Union


class EasedValue(ParameterSource):
    """
    The parameter source in which the value is obtained
    by using an easing function.
    """

    @property
    def start_value(
        self
    ) -> float:
        """
        The start value of this eased ParameterSource.
        """
        return self._easing_animated_function.start_value
    
    @property
    def end_value(
        self
    ) -> float:
        """
        The end value of this eased ParameterSource.
        """
        return self._easing_animated_function.end_value

    def __init__(
        self,
        start_value: float,
        end_value: float,
        easing_function_name: Union[EasingFunctionName, str],
        # time_source: EvaluationContext
    ):
        easing_function_name = EasingFunctionName.to_enum(easing_function_name)

        self._easing_animated_function: EasingAnimatedFunction = EasingAnimatedFunction.get(easing_function_name)(
            start_value = start_value,
            end_value = end_value
            # By now the 'duration' is not important at all
        )
        """
        *For internal use only*

        The internal easing animated function that will be
        able to calculate the values.
        """

    def evaluate(
        self,
        context: EvaluationContext
    ) -> float:
        """
        Get the value for the `context` provided. In this
        case, we will use the `t` normalized time moment
        that is set in the context.

        The value is the real value, not normalized.
        """
        return self._easing_animated_function.get_value_from_t_normalized(
            t_normalized = context.t
        )
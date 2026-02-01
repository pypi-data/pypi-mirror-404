from yta_parameters.abstract import Parameter
from yta_parameters.context.time import TimeEvaluationContext
from yta_math_easings.abstract import EasingFunctionName
from yta_math_easings.animated.abstract import EasingAnimatedFunction
from typing import Union


# TODO: Rename to 'EasedTimeParameter' (?)
class EasedParameter(Parameter):
    """
    A parameter to be used within a time context that
    uses easing functions to calculate the values.
    """

    @property
    def start_value(
        self
    ) -> float:
        """
        The start value of this eased parameter.
        """
        return self._easing_animated_function.start_value
    
    @property
    def end_value(
        self
    ) -> float:
        """
        The end value of this eased parameter.
        """
        return self._easing_animated_function.end_value

    def __init__(
        self,
        start_value: float,
        end_value: float,
        easing_function_name: Union[EasingFunctionName, str] = 'linear'
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
        evaluation_context: TimeEvaluationContext,
    ) -> float:
        """
        Get the value using the `evaluation_context`
        provided.

        This method will return the real not normalized
        value.
        """
        return self._easing_animated_function.get_value_from_t_normalized(
            t_normalized = evaluation_context.t_normalized
        )
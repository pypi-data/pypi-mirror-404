from yta_parameters.context.abstract import EvaluationContext
from yta_parameters.types import BASIC_NON_ITERABLE_TYPE
from yta_parameters.abstract import Parameter


class ConstantParameter(Parameter):
    """
    A parameter that has always the same value and
    is unaware of the context.
    """

    def __init__(
        self,
        value: BASIC_NON_ITERABLE_TYPE
    ):
        self.value: BASIC_NON_ITERABLE_TYPE = value
        """
        The constant value of this parameter.
        """

    # TODO: I don't know if this class is ok because
    # it uses a general context
    def evaluate(
        self,
        # This is mandatory, even though it is not used
        evaluation_context: EvaluationContext
    ):
        return self.value
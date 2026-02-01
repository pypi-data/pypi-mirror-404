from yta_parameters.context.abstract import EvaluationContext
from yta_validation.parameter import ParameterValidator


class TimeEvaluationContext(EvaluationContext):
    """
    Evaluation context that includes a normalized
    time moment to use when evaluating the parameter.
    """

    def __init__(
        self,
        t_normalized: float
    ):
        ParameterValidator.validate_mandatory_number_between('t_normalized', t_normalized, 0.0, 1.0)

        self.t_normalized: float = t_normalized
        """
        The normalized time moment in which the parameter
        must be evaluated.
        """
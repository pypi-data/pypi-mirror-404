from yta_parameters.context.abstract import EvaluationContext


class TimeEvaluationContext(EvaluationContext):
    """
    Evaluation context that includes a time moment
    to use when evaluating the parameter.
    """

    def __init__(
        self,
        t: float
    ):
        self.t: float = t
        """
        The time moment in which the parameter must be
        evaluated.
        """
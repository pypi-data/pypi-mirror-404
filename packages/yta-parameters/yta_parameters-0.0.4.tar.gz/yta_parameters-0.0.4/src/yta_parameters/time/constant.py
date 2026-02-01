from yta_parameters import ConstantParameter as BaseConstantParameter
from yta_parameters.context.time import TimeEvaluationContext


# TODO: Rename to 'ConstantTimeParameter' (?)
class ConstantParameter(BaseConstantParameter):
    """
    A parameter to be used within a time context but
    returning always the same value.
    """

    def evaluate(
        self,
        evaluation_context: TimeEvaluationContext,
    ) -> float:
        """
        Get the value using (ignoring, actually) the
        `evaluation_context` provided.

        This method will return the real not normalized
        value.
        """
        return self.value
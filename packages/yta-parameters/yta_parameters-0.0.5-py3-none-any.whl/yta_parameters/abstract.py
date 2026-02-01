from yta_parameters.context.abstract import EvaluationContext
from abc import ABC, abstractmethod


class Parameter(ABC):
    """
    *Abstract class*

    Abstract class to identify a parameter that must
    be evaluated based on a context.
    """

    @abstractmethod
    def evaluate(
        self,
        evaluation_context: EvaluationContext
    ):
        """
        Evaluate the parameter based on the provided
        `evaluation_context`.

        This method will return the real not normalized
        value.
        """
        pass
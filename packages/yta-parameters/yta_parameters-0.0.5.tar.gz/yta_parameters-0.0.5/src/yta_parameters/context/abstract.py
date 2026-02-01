
from dataclasses import dataclass
from abc import ABC


@dataclass
class EvaluationContext(ABC):
    """
    *Abstract class*

    Abstract class to identify a context that will be
    used to evaluate the value a parameter must have.
    """

    pass
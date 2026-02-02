from yta_editor_parameters.context import VideoEditorEvaluationContext
from yta_editor_parameters.abstract import VideoEditorParameter
from yta_parameters.types import BASIC_NON_ITERABLE_TYPE


class ConstantVideoEditorParameter(VideoEditorParameter):
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

    def evaluate(
        self,
        # This is mandatory, even though it is not used
        evaluation_context: VideoEditorEvaluationContext
    ):
        return self.value
from yta_editor_parameters.context import VideoEditorEvaluationContext
from yta_editor_parameters.abstract import VideoEditorParameter


class ConstantVideoEditorParameter(VideoEditorParameter):
    """
    A parameter that has always the same value and
    is unaware of the context.
    """

    def __init__(
        self,
        # TODO: Maybe use 'BASIC_TYPE'
        value: any
    ):
        self.value: any = value
        """
        The constant value of this parameter.
        """

    def evaluate(
        self,
        # This is mandatory, even though it is not used
        evaluation_context: VideoEditorEvaluationContext
    ):
        return self.value